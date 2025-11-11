"""Common API dependencies for authentication and authorization."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import ApiToken, NotificationEndpoint, Restaurant
from ..services.auth import InvalidApiKey, verify_api_key


def require_authenticated_restaurant(
    restaurant_id: int,
    session: Session = Depends(get_session),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Restaurant:
    """Ensure the caller has access to the target restaurant."""

    token = _validate_api_key(session, api_key)
    restaurant = token.restaurant
    if restaurant.id != restaurant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Forbidden for this restaurant")
    if not restaurant.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Restaurant is inactive")
    return restaurant


def optional_authenticated_restaurant(
    session: Session = Depends(get_session),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Restaurant | None:
    """Return the authenticated restaurant if an API key is provided."""

    if api_key is None:
        return None
    token = _validate_api_key(session, api_key)
    restaurant = token.restaurant
    if not restaurant.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Restaurant is inactive")
    return restaurant


def require_api_token(
    token_id: int,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> ApiToken:
    """Load an API token for the authenticated restaurant."""

    token = (
        session.query(ApiToken)
        .filter(ApiToken.id == token_id, ApiToken.restaurant_id == restaurant.id)
        .one_or_none()
    )
    if token is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="API token not found")
    return token


def require_notification_endpoint(
    endpoint_id: int,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> NotificationEndpoint:
    endpoint = (
        session.query(NotificationEndpoint)
        .filter(
            NotificationEndpoint.id == endpoint_id,
            NotificationEndpoint.restaurant_id == restaurant.id,
        )
        .one_or_none()
    )
    if endpoint is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Notification endpoint not found")
    return endpoint


def _validate_api_key(session: Session, api_key: str | None) -> ApiToken:
    if not api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="API key required")
    api_key = api_key.strip()
    try:
        return verify_api_key(session, api_key)
    except InvalidApiKey as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


__all__ = [
    "require_authenticated_restaurant",
    "optional_authenticated_restaurant",
    "require_api_token",
    "require_notification_endpoint",
]
