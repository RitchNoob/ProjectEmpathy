"""Call session endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import CallSession, Restaurant
from ..schemas import CallSessionCreate, CallSessionRead
from ..db import get_session
from ..services.notifications import dispatch_notification
from .dependencies import require_authenticated_restaurant

router = APIRouter(prefix="/restaurants/{restaurant_id}/calls", tags=["calls"])


@router.get("/", response_model=list[CallSessionRead])
def list_calls(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> list[CallSession]:
    return (
        session.query(CallSession)
        .filter(CallSession.restaurant_id == restaurant.id)
        .order_by(CallSession.created_at.desc())
        .all()
    )


@router.post("/", response_model=CallSessionRead, status_code=status.HTTP_201_CREATED)
def create_call_session(
    payload: CallSessionCreate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> CallSession:
    call = CallSession(restaurant_id=restaurant.id, **payload.model_dump())
    session.add(call)
    session.flush()
    dispatch_notification(
        session,
        restaurant.id,
        "calls.created",
        CallSessionRead.model_validate(call).model_dump(),
    )
    return call


__all__ = ["router"]
