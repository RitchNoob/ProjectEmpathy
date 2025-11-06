"""Restaurant CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import Restaurant
from ..schemas import RestaurantCreate, RestaurantRead, RestaurantUpdate
from ..db import get_session

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("/", response_model=list[RestaurantRead])
def list_restaurants(session: Session = Depends(get_session)) -> list[Restaurant]:
    return session.query(Restaurant).all()


@router.post("/", response_model=RestaurantRead, status_code=status.HTTP_201_CREATED)
def create_restaurant(payload: RestaurantCreate, session: Session = Depends(get_session)) -> Restaurant:
    restaurant = Restaurant(**payload.model_dump())
    session.add(restaurant)
    session.flush()
    return restaurant


@router.get("/{restaurant_id}", response_model=RestaurantRead)
def get_restaurant(restaurant_id: int, session: Session = Depends(get_session)) -> Restaurant:
    restaurant = session.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant


@router.patch("/{restaurant_id}", response_model=RestaurantRead)
def update_restaurant(restaurant_id: int, payload: RestaurantUpdate, session: Session = Depends(get_session)) -> Restaurant:
    restaurant = session.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(restaurant, key, value)
    session.add(restaurant)
    session.flush()
    return restaurant


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_restaurant(restaurant_id: int, session: Session = Depends(get_session)) -> None:
    restaurant = session.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    restaurant.is_active = False
    session.add(restaurant)
