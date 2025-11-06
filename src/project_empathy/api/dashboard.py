"""Dashboard metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models import Restaurant
from ..schemas import DashboardStats
from ..services.statistics import compute_dashboard_stats
from ..db import get_session

router = APIRouter(prefix="/restaurants/{restaurant_id}/dashboard", tags=["dashboard"])


def _get_restaurant(session: Session, restaurant_id: int) -> Restaurant:
    restaurant = session.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.get("/stats", response_model=DashboardStats)
def get_stats(restaurant_id: int, session: Session = Depends(get_session)) -> DashboardStats:
    _get_restaurant(session, restaurant_id)
    return compute_dashboard_stats(session, restaurant_id)


__all__ = ["router"]
