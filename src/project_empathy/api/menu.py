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
from .dependencies import require_authenticated_restaurant

router = APIRouter(prefix="/restaurants/{restaurant_id}/menu", tags=["menu"])


@router.get("/items", response_model=list[MenuItemRead])
def list_items(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> list[MenuItem]:
    return (
        session.query(MenuItem)
        .filter(MenuItem.restaurant_id == restaurant.id)
        .order_by(MenuItem.name.asc())
        .all()
    )


@router.post("/items", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: MenuItemCreate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> MenuItem:
    item = MenuItem(restaurant_id=restaurant.id, **payload.model_dump())
    session.add(item)
    session.flush()
    return item


@router.patch("/items/{item_id}", response_model=MenuItemRead)
def update_item(
    item_id: int,
    payload: MenuItemUpdate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> MenuItem:
    item = session.get(MenuItem, item_id)
    if not item or item.restaurant_id != restaurant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    session.add(item)
    session.flush()
    return item


@router.get("/categories", response_model=list[MenuCategoryRead])
def list_categories(
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> list[MenuCategory]:
    return (
        session.query(MenuCategory)
        .filter(MenuCategory.restaurant_id == restaurant.id)
        .order_by(MenuCategory.name.asc())
        .all()
    )


@router.post("/categories", response_model=MenuCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: MenuCategoryCreate,
    restaurant: Restaurant = Depends(require_authenticated_restaurant),
    session: Session = Depends(get_session),
) -> MenuCategory:
    category = MenuCategory(restaurant_id=restaurant.id, **payload.model_dump())
    session.add(category)
    session.flush()
    return category


__all__ = ["router"]
