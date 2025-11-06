"""Dashboard metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models import Restaurant
from ..schemas import DashboardStats
from ..services.statistics import compute_dashboard_stats
from ..db import get_session
from .dependencies import require_authenticated_restaurant

router = APIRouter(prefix="/restaurants/{restaurant_id}/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> DashboardStats:
    return compute_dashboard_stats(session, restaurant.id)


__all__ = ["router"]
