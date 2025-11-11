"""Notification endpoint management APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import NotificationEndpoint, Restaurant
from ..schemas import (
    NotificationEndpointCreate,
    NotificationEndpointRead,
    NotificationEndpointUpdate,
    NotificationTestRequest,
)
from ..services.notifications import NotificationDispatcher, get_notification_dispatcher
from .dependencies import (
    require_authenticated_restaurant,
    require_notification_endpoint,
)


router = APIRouter(prefix="/restaurants/{restaurant_id}/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationEndpointRead])
def list_endpoints(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> list[NotificationEndpoint]:
    return (
        session.query(NotificationEndpoint)
        .filter(NotificationEndpoint.restaurant_id == restaurant.id)
        .order_by(NotificationEndpoint.created_at.asc())
        .all()
    )


@router.post("/", response_model=NotificationEndpointRead, status_code=status.HTTP_201_CREATED)
def create_endpoint(
    payload: NotificationEndpointCreate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> NotificationEndpoint:
    endpoint = NotificationEndpoint(
        restaurant_id=restaurant.id,
        name=payload.name,
        target_url=str(payload.target_url),
        events=payload.events,
        secret=payload.secret,
    )
    session.add(endpoint)
    session.flush()
    return endpoint


@router.patch("/{endpoint_id}", response_model=NotificationEndpointRead)
def update_endpoint(
    payload: NotificationEndpointUpdate,
    endpoint: NotificationEndpoint = Depends(require_notification_endpoint),
    session: Session = Depends(get_session),
) -> NotificationEndpoint:
    updates = payload.model_dump(exclude_unset=True)
    if "target_url" in updates and updates["target_url"] is not None:
        updates["target_url"] = str(updates["target_url"])
    for field, value in updates.items():
        setattr(endpoint, field, value)
    session.add(endpoint)
    session.flush()
    return endpoint


@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_endpoint(
    endpoint: NotificationEndpoint = Depends(require_notification_endpoint),
    session: Session = Depends(get_session),
) -> None:
    session.delete(endpoint)
    session.flush()


@router.post("/{endpoint_id}/test", response_model=NotificationEndpointRead)
def send_test_notification(
    payload: NotificationTestRequest,
    endpoint: NotificationEndpoint = Depends(require_notification_endpoint),
    session: Session = Depends(get_session),
    dispatcher: NotificationDispatcher = Depends(get_notification_dispatcher),
) -> NotificationEndpoint:
    dispatcher.dispatch(
        session,
        [endpoint],
        payload.event_type,
        payload.payload or {"message": "Test notification from Project Empathy"},
    )
    session.refresh(endpoint)
    return endpoint


__all__ = ["router"]
