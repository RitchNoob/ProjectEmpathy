"""Order endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import Order, Restaurant
from ..schemas import OrderCreate, OrderRead, OrderStatusUpdate
from ..services.orders import MenuItemUnavailableError, OrderNotFoundError, create_order, mark_order_status
from ..services.subscriptions import SubscriptionError, ensure_active_subscription, record_usage
from ..db import get_session
from .dependencies import require_authenticated_restaurant

router = APIRouter(prefix="/restaurants/{restaurant_id}/orders", tags=["orders"])


@router.get("/", response_model=list[OrderRead])
def list_orders(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> list[Order]:
    return (
        session.query(Order)
        .filter(Order.restaurant_id == restaurant.id)
        .order_by(Order.created_at.desc())
        .all()
    )


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order_endpoint(
    payload: OrderCreate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> Order:
    try:
        subscription = ensure_active_subscription(session, restaurant.id)
    except SubscriptionError as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc

    try:
        order = create_order(session, restaurant, payload)
    except MenuItemUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    record_usage(session, subscription, metric="orders", amount=1, metadata=f"order:{order.id}")
    return order


@router.post("/{order_id}/status", response_model=OrderRead)
def update_status(
    order_id: int,
    payload: OrderStatusUpdate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> Order:
    try:
        return mark_order_status(session, order_id, payload.status)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


__all__ = ["router"]
