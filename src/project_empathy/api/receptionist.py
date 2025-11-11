"""Endpoints to configure the AI receptionist persona and branding."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import ReceptionistProfile, Restaurant
from ..schemas import (
    ReceptionistPreview,
    ReceptionistProfileRead,
    ReceptionistProfileUpdate,
)
from ..services.receptionist import build_profile_preview
from .dependencies import require_authenticated_restaurant


router = APIRouter(prefix="/restaurants/{restaurant_id}/receptionist", tags=["receptionist"])


def _ensure_profile(session: Session, restaurant: Restaurant) -> ReceptionistProfile:
    profile = restaurant.receptionist_profile
    if profile is None:
        profile = ReceptionistProfile(restaurant=restaurant)
        session.add(profile)
        session.flush()
        session.refresh(restaurant)
    return profile


@router.get("/profile", response_model=ReceptionistProfileRead)
def get_profile(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> ReceptionistProfile:
    """Return the personalised AI receptionist profile for the restaurant."""

    return _ensure_profile(session, restaurant)


@router.patch("/profile", response_model=ReceptionistProfileRead)
def update_profile(
    payload: ReceptionistProfileUpdate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> ReceptionistProfile:
    """Update the receptionist persona, returning the updated profile."""

    profile = _ensure_profile(session, restaurant)
    update_data = payload.model_dump(exclude_unset=True)
    if "upsell_phrases" in update_data and update_data["upsell_phrases"] is None:
        update_data["upsell_phrases"] = []
    for key, value in update_data.items():
        setattr(profile, key, value)
    session.add(profile)
    session.flush()
    return profile


@router.get("/preview", response_model=ReceptionistPreview)
def preview_profile(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    """Return a rich preview of the concierge behaviour for the UI."""

    profile = _ensure_profile(session, restaurant)
    return build_profile_preview(profile)


__all__ = ["router"]
