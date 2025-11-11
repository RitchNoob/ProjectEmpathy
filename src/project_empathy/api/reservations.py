"""Reservation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import Reservation, Restaurant
from ..schemas import ReservationCreate, ReservationRead
from ..services.notifications import dispatch_notification
from ..services.subscriptions import SubscriptionError, ensure_active_subscription, record_usage
from ..db import get_session
from .dependencies import require_authenticated_restaurant

router = APIRouter(prefix="/restaurants/{restaurant_id}/reservations", tags=["reservations"])


@router.get("/", response_model=list[ReservationRead])
def list_reservations(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> list[Reservation]:
    return (
        session.query(Reservation)
        .filter(Reservation.restaurant_id == restaurant.id)
        .order_by(Reservation.reservation_time.desc())
        .all()
    )


@router.post("/", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> Reservation:
    try:
        subscription = ensure_active_subscription(session, restaurant.id)
    except SubscriptionError as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc

    reservation = Reservation(restaurant_id=restaurant.id, **payload.model_dump())
    session.add(reservation)
    session.flush()
    dispatch_notification(
        session,
        restaurant.id,
        "reservations.created",
        ReservationRead.model_validate(reservation).model_dump(),
    )
    record_usage(session, subscription, metric="reservations", amount=1, metadata=f"reservation:{reservation.id}")
    return reservation


__all__ = ["router"]
