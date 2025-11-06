import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from project_empathy.config import get_settings
from project_empathy.main import create_app
from project_empathy.db import Base, SessionLocal, reset_engine_cache


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
            "timezone": "Europe/Paris"
        },
    )
    restaurant = response.json()

    plan = test_client.post(
        "/api/v1/subscriptions/plans",
        json={
            "external_id": "plan-test",
            "name": "Plan Test",
            "monthly_price": "99.00",
            "call_quota": 100
        },
    ).json()

    now = datetime.utcnow()
    test_client.post(
        f"/api/v1/subscriptions/restaurants/{restaurant['id']}",
        json={
            "plan_id": plan["id"],
            "status": "active",
            "current_period_start": (now - timedelta(days=1)).isoformat(),
            "current_period_end": (now + timedelta(days=29)).isoformat(),
            "credits_remaining": 50
        },
    )
    return restaurant
