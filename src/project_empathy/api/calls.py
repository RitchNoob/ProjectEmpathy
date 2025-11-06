"""Call session endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import CallSession, Restaurant
from ..schemas import CallSessionCreate, CallSessionRead
from ..db import get_session

router = APIRouter(prefix="/restaurants/{restaurant_id}/calls", tags=["calls"])


def _get_restaurant(session: Session, restaurant_id: int) -> Restaurant:
    restaurant = session.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant


@router.get("/", response_model=list[CallSessionRead])
def list_calls(restaurant_id: int, session: Session = Depends(get_session)) -> list[CallSession]:
    _get_restaurant(session, restaurant_id)
    return (
        session.query(CallSession)
        .filter(CallSession.restaurant_id == restaurant_id)
        .order_by(CallSession.created_at.desc())
        .all()
    )


@router.post("/", response_model=CallSessionRead, status_code=status.HTTP_201_CREATED)
def create_call_session(
    restaurant_id: int, payload: CallSessionCreate, session: Session = Depends(get_session)
) -> CallSession:
    restaurant = _get_restaurant(session, restaurant_id)
    call = CallSession(restaurant=restaurant, **payload.model_dump())
    session.add(call)
    session.flush()
    return call


__all__ = ["router"]
