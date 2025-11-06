"""Aggregate statistics for the dashboard."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import CallSession, Order
from ..schemas import DashboardStats


def compute_dashboard_stats(session: Session, restaurant_id: int) -> DashboardStats:
    """Return aggregated metrics for the dashboard UI."""

    total_calls = session.query(func.count(CallSession.id)).filter(CallSession.restaurant_id == restaurant_id).scalar() or 0
    total_orders = session.query(func.count(Order.id)).filter(Order.restaurant_id == restaurant_id).scalar() or 0
    raw_revenue = (
        session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(Order.restaurant_id == restaurant_id).scalar() or 0
    )
    total_revenue = Decimal(str(raw_revenue))
    average_order_value = Decimal("0")
    if total_orders:
        average_order_value = (total_revenue / Decimal(total_orders)).quantize(Decimal("0.01"))

    return DashboardStats(
        total_calls=int(total_calls),
        total_orders=int(total_orders),
        total_revenue=total_revenue.quantize(Decimal("0.01")) if total_revenue else Decimal("0"),
        average_order_value=average_order_value,
    )


__all__ = ["compute_dashboard_stats"]
