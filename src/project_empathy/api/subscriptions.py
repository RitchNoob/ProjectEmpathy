"""Subscription management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import Restaurant, Subscription, SubscriptionPlan
from ..schemas import SubscriptionCreate, SubscriptionPlanCreate, SubscriptionPlanRead, SubscriptionRead
from ..db import get_session

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans", response_model=list[SubscriptionPlanRead])
def list_plans(session: Session = Depends(get_session)) -> list[SubscriptionPlan]:
    return session.query(SubscriptionPlan).order_by(SubscriptionPlan.monthly_price.asc()).all()


@router.post("/plans", response_model=SubscriptionPlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(payload: SubscriptionPlanCreate, session: Session = Depends(get_session)) -> SubscriptionPlan:
    existing = session.query(SubscriptionPlan).filter_by(external_id=payload.external_id).one_or_none()
    data = payload.model_dump()
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        session.add(existing)
        session.flush()
        return existing

    plan = SubscriptionPlan(**data)
    session.add(plan)
    session.flush()
    return plan


@router.post("/restaurants/{restaurant_id}", response_model=SubscriptionRead)
def create_subscription(
    restaurant_id: int, payload: SubscriptionCreate, session: Session = Depends(get_session)
) -> Subscription:
    restaurant = session.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    plan = session.get(SubscriptionPlan, payload.plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")

    subscription = session.query(Subscription).filter_by(restaurant_id=restaurant.id).one_or_none()
    if subscription:
        for key, value in payload.model_dump().items():
            setattr(subscription, key, value)
    else:
        subscription = Subscription(restaurant=restaurant, **payload.model_dump())
        session.add(subscription)
    session.flush()
    return subscription


@router.get("/restaurants/{restaurant_id}", response_model=SubscriptionRead)
def get_subscription(restaurant_id: int, session: Session = Depends(get_session)) -> Subscription:
    subscription = session.query(Subscription).filter_by(restaurant_id=restaurant_id).one_or_none()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription


__all__ = ["router"]
