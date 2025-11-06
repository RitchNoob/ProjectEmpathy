"""Subscription and usage tracking helpers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Subscription, SubscriptionPlan, UsageRecord


class SubscriptionError(RuntimeError):
    """Generic subscription failure."""


def ensure_active_subscription(session: Session, restaurant_id: int) -> Subscription:
    """Ensure the restaurant has an active subscription."""

    subscription = (
        session.query(Subscription)
        .filter(Subscription.restaurant_id == restaurant_id, Subscription.status == "active")
        .one_or_none()
    )
    if not subscription:
        raise SubscriptionError("Active subscription required to access this feature")

    now = datetime.utcnow()
    if subscription.current_period_end < now:
        subscription.status = "past_due"
        session.add(subscription)
        raise SubscriptionError("Subscription period has expired")
    return subscription


def record_usage(session: Session, subscription: Subscription, metric: str, amount: int, metadata: str | None = None) -> UsageRecord:
    """Create a usage record and decrement credits/quota if applicable."""

    if subscription.credits_remaining is not None and subscription.credits_remaining > 0:
        subscription.credits_remaining = max(subscription.credits_remaining - amount, 0)
        session.add(subscription)

    usage = UsageRecord(subscription=subscription, metric=metric, amount=amount, metadata=metadata)
    session.add(usage)
    session.flush()
    return usage


def sync_subscription_plan(session: Session, payload: dict) -> SubscriptionPlan:
    """Insert or update a subscription plan from Flexprice/Stripe payload."""

    plan = session.query(SubscriptionPlan).filter_by(external_id=payload["id"]).one_or_none()
    if plan:
        plan.name = payload.get("name", plan.name)
        plan.description = payload.get("description", plan.description)
        plan.monthly_price = payload.get("monthly_price", plan.monthly_price)
        plan.call_quota = payload.get("call_quota", plan.call_quota)
    else:
        plan = SubscriptionPlan(
            external_id=payload["id"],
            name=payload.get("name", payload["id"]),
            description=payload.get("description"),
            monthly_price=payload.get("monthly_price", 0),
            call_quota=payload.get("call_quota", 0),
        )
        session.add(plan)
    session.flush()
    return plan


__all__ = ["ensure_active_subscription", "record_usage", "sync_subscription_plan", "SubscriptionError"]
