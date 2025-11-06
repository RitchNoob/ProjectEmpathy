"""Menu endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import MenuCategory, MenuItem, Restaurant
from ..schemas import (
    MenuCategoryCreate,
    MenuCategoryRead,
    MenuItemCreate,
    MenuItemRead,
    MenuItemUpdate,
)
from ..db import get_session

router = APIRouter(prefix="/restaurants/{restaurant_id}/menu", tags=["menu"])


def _get_restaurant(session: Session, restaurant_id: int) -> Restaurant:
    restaurant = session.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant


@router.get("/items", response_model=list[MenuItemRead])
def list_items(restaurant_id: int, session: Session = Depends(get_session)) -> list[MenuItem]:
    _get_restaurant(session, restaurant_id)
    return (
        session.query(MenuItem)
        .filter(MenuItem.restaurant_id == restaurant_id)
        .order_by(MenuItem.name.asc())
        .all()
    )


@router.post("/items", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
def create_item(
    restaurant_id: int, payload: MenuItemCreate, session: Session = Depends(get_session)
) -> MenuItem:
    restaurant = _get_restaurant(session, restaurant_id)
    item = MenuItem(restaurant=restaurant, **payload.model_dump())
    session.add(item)
    session.flush()
    return item


@router.patch("/items/{item_id}", response_model=MenuItemRead)
def update_item(
    restaurant_id: int,
    item_id: int,
    payload: MenuItemUpdate,
    session: Session = Depends(get_session),
) -> MenuItem:
    _get_restaurant(session, restaurant_id)
    item = session.get(MenuItem, item_id)
    if not item or item.restaurant_id != restaurant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    session.add(item)
    session.flush()
    return item


@router.get("/categories", response_model=list[MenuCategoryRead])
def list_categories(restaurant_id: int, session: Session = Depends(get_session)) -> list[MenuCategory]:
    _get_restaurant(session, restaurant_id)
    return (
        session.query(MenuCategory)
        .filter(MenuCategory.restaurant_id == restaurant_id)
        .order_by(MenuCategory.name.asc())
        .all()
    )


@router.post("/categories", response_model=MenuCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    restaurant_id: int, payload: MenuCategoryCreate, session: Session = Depends(get_session)
) -> MenuCategory:
    restaurant = _get_restaurant(session, restaurant_id)
    category = MenuCategory(restaurant=restaurant, **payload.model_dump())
    session.add(category)
    session.flush()
    return category


__all__ = ["router"]
