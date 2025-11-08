"""Endpoints to manage API tokens for restaurants."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import ApiToken, Restaurant
from ..schemas import ApiTokenCreate, ApiTokenProvisioned, ApiTokenRead
from ..services.auth import issue_api_token, revoke_api_token, rotate_api_token
from .dependencies import require_api_token, require_authenticated_restaurant


router = APIRouter(prefix="/restaurants/{restaurant_id}/api-tokens", tags=["api-tokens"])


@router.get("/", response_model=list[ApiTokenRead])
def list_tokens(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> list[ApiToken]:
    return (
        session.query(ApiToken)
        .filter(ApiToken.restaurant_id == restaurant.id)
        .order_by(ApiToken.created_at.asc())
        .all()
    )


@router.post("/", response_model=ApiTokenProvisioned, status_code=status.HTTP_201_CREATED)
def create_token(
    payload: ApiTokenCreate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> ApiTokenProvisioned:
    token, raw = issue_api_token(session, restaurant, payload.name)
    return ApiTokenProvisioned(token=raw, metadata=token)


@router.post("/{token_id}/rotate", response_model=ApiTokenProvisioned)
def rotate_token(
    token: ApiToken = Depends(require_api_token),
    session: Session = Depends(get_session),
) -> ApiTokenProvisioned:
    raw = rotate_api_token(session, token)
    return ApiTokenProvisioned(token=raw, metadata=token)


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_token(
    token: ApiToken = Depends(require_api_token),
    session: Session = Depends(get_session),
) -> None:
    revoke_api_token(session, token)


__all__ = ["router"]
