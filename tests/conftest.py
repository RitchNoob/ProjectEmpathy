import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from project_empathy.config import get_settings
from project_empathy.main import create_app
from project_empathy.db import Base, SessionLocal, reset_engine_cache
from project_empathy.models import Restaurant as RestaurantModel, Subscription, SubscriptionPlan
from project_empathy.services import notifications as notifications_service
from project_empathy.services.auth import issue_api_token


@pytest.fixture(scope="session")
def test_client():
    os.environ["EMP_DATABASE__URL"] = "sqlite:///:memory:"
    get_settings.cache_clear()  # type: ignore[attr-defined]
    reset_engine_cache()
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal.configure(bind=engine)  # type: ignore[attr-defined]
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def seeded_restaurant(test_client):
    response = test_client.post(
        "/api/v1/restaurants/",
        json={
            "name": "Chez Test",
            "email": "test@example.com",
            "phone_number": "+33123456789",
            "timezone": "Europe/Paris",
        },
    )
    restaurant = response.json()

    with SessionLocal() as session:
        db_restaurant = session.get(RestaurantModel, restaurant["id"])
        _, api_key = issue_api_token(session, db_restaurant, "Tests API")
        session.commit()

    restaurant["api_key"] = api_key
    restaurant["headers"] = {"X-API-Key": api_key}

    with SessionLocal() as session:
        plan = (
            session.query(SubscriptionPlan)
            .filter_by(external_id="plan-test")
            .one_or_none()
        )
        if plan is None:
            plan = SubscriptionPlan(
                external_id="plan-test",
                name="Plan Test",
                monthly_price="99.00",
                call_quota=100,
            )
            session.add(plan)
            session.flush()

        subscription = (
            session.query(Subscription)
            .filter_by(restaurant_id=restaurant["id"])
            .one_or_none()
        )
        if subscription is None:
            subscription = Subscription(
                restaurant_id=restaurant["id"],
                plan_id=plan.id,
                status="active",
                current_period_start=datetime.utcnow() - timedelta(days=1),
                current_period_end=datetime.utcnow() + timedelta(days=29),
                credits_remaining=50,
            )
        else:
            subscription.plan_id = plan.id
            subscription.status = "active"
            subscription.current_period_start = datetime.utcnow() - timedelta(days=1)
            subscription.current_period_end = datetime.utcnow() + timedelta(days=29)
            subscription.credits_remaining = 50
        session.add(subscription)
        session.commit()
    return restaurant


@pytest.fixture()
def notification_events(monkeypatch):
    notifications_service.get_notification_dispatcher.cache_clear()
    events: list[dict] = []

    def fake_dispatch(self, session, endpoints, event_type, payload):  # type: ignore[override]
        active_endpoints = [
            endpoint
            for endpoint in endpoints
            if endpoint.is_active and (not endpoint.events or event_type in endpoint.events)
        ]
        if not active_endpoints:
            return

        events.append(
            {
                "event": event_type,
                "payload": payload,
                "endpoint_ids": [endpoint.id for endpoint in active_endpoints],
            }
        )
        now = datetime.utcnow()
        for endpoint in active_endpoints:
            endpoint.last_status_code = 200
            endpoint.last_error = None
            endpoint.last_delivery_at = now
            session.add(endpoint)
        session.flush()

    monkeypatch.setattr(
        notifications_service.NotificationDispatcher,
        "dispatch",
        fake_dispatch,
        raising=False,
    )

    yield events

    notifications_service.get_notification_dispatcher.cache_clear()
