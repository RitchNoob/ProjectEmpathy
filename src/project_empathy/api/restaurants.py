"""Restaurant CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import ReceptionistProfile, Restaurant
from ..schemas import RestaurantCreate, RestaurantRead, RestaurantUpdate
from ..db import get_session
from .dependencies import optional_authenticated_restaurant, require_authenticated_restaurant

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("/", response_model=list[RestaurantRead])
def list_restaurants(
    session: Session = Depends(get_session),
    current: Restaurant | None = Depends(optional_authenticated_restaurant),
) -> list[Restaurant]:
    if current:
        return [current]
    return session.query(Restaurant).all()


@router.post("/", response_model=RestaurantRead, status_code=status.HTTP_201_CREATED)
def create_restaurant(payload: RestaurantCreate, session: Session = Depends(get_session)) -> Restaurant:
    restaurant = Restaurant(**payload.model_dump())
    session.add(restaurant)
    if restaurant.receptionist_profile is None:
        session.add(ReceptionistProfile(restaurant=restaurant))
    session.flush()
    return restaurant


@router.get("/{restaurant_id}", response_model=RestaurantRead)
def get_restaurant(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
) -> Restaurant:
    return restaurant


@router.patch("/{restaurant_id}", response_model=RestaurantRead)
def update_restaurant(
    payload: RestaurantUpdate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> Restaurant:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(restaurant, key, value)
    session.add(restaurant)
    session.flush()
    return restaurant


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_restaurant(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> None:
    restaurant.is_active = False
    session.add(restaurant)
