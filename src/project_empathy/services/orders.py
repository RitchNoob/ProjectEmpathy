"""Business logic for managing orders."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from ..models import MenuItem, Order, OrderItem, Restaurant
from ..schemas import OrderCreate


class OrderNotFoundError(RuntimeError):
    """Raised when an order is missing."""


class MenuItemUnavailableError(RuntimeError):
    """Raised when attempting to order an unavailable item."""


def create_order(session: Session, restaurant: Restaurant, payload: OrderCreate) -> Order:
    """Create an order, computing totals and validating menu availability."""

    order = Order(
        restaurant=restaurant,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        delivery_address=payload.delivery_address,
        status=payload.status,
    )

    total = Decimal("0")
    for item_payload in payload.items:
        menu_item = session.get(MenuItem, item_payload.menu_item_id)
        if not menu_item or menu_item.restaurant_id != restaurant.id:
            raise MenuItemUnavailableError(f"Menu item {item_payload.menu_item_id} unavailable")
        if not menu_item.is_available:
            raise MenuItemUnavailableError(f"Menu item {menu_item.name} is not currently available")

        line_total = menu_item.price * item_payload.quantity
        total += line_total
        order.items.append(
            OrderItem(menu_item=menu_item, quantity=item_payload.quantity, notes=item_payload.notes)
        )

    order.total_amount = total
    session.add(order)
    session.flush()
    return order


def mark_order_status(session: Session, order_id: int, status: str) -> Order:
    """Update the status of an order."""

    order = session.get(Order, order_id)
    if not order:
        raise OrderNotFoundError(f"Order {order_id} not found")
    order.status = status
    session.add(order)
    session.flush()
    return order


__all__ = ["create_order", "mark_order_status", "OrderNotFoundError", "MenuItemUnavailableError"]
