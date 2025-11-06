"""Reservation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import Reservation, Restaurant
from ..schemas import ReservationCreate, ReservationRead
from ..services.subscriptions import SubscriptionError, ensure_active_subscription, record_usage
from ..db import get_session

router = APIRouter(prefix="/restaurants/{restaurant_id}/reservations", tags=["reservations"])


def _get_restaurant(session: Session, restaurant_id: int) -> Restaurant:
    restaurant = session.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant


@router.get("/", response_model=list[ReservationRead])
def list_reservations(restaurant_id: int, session: Session = Depends(get_session)) -> list[Reservation]:
    _get_restaurant(session, restaurant_id)
    return (
        session.query(Reservation)
        .filter(Reservation.restaurant_id == restaurant_id)
        .order_by(Reservation.reservation_time.desc())
        .all()
    )


@router.post("/", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def create_reservation(
    restaurant_id: int, payload: ReservationCreate, session: Session = Depends(get_session)
) -> Reservation:
    restaurant = _get_restaurant(session, restaurant_id)
    try:
        subscription = ensure_active_subscription(session, restaurant.id)
    except SubscriptionError as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc

    reservation = Reservation(restaurant=restaurant, **payload.model_dump())
    session.add(reservation)
    session.flush()
    record_usage(session, subscription, metric="reservations", amount=1, metadata=f"reservation:{reservation.id}")
    return reservation


__all__ = ["router"]
