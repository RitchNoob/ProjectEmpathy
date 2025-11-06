"""Utilities to turn Project Empathy into a turnkey demo environment."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import Base, SessionLocal, get_engine
from .models import (
    CallSession,
    MenuCategory,
    MenuItem,
    Order,
    OrderItem,
    Reservation,
    Restaurant,
    Subscription,
    SubscriptionPlan,
    UsageRecord,
)


def create_schema(engine: Optional[object] = None) -> object:
    """Create all database tables using the configured engine."""

    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(bind=engine)
    SessionLocal.configure(bind=engine)
    _ensure_storage_dirs()
    return engine


def seed_demo_data(session: Optional[Session] = None, *, skip_existing: bool = True) -> bool:
    """Populate the database with a realistic restaurant, menu and usage data."""

    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        if skip_existing and session.execute(select(Restaurant.id).limit(1)).first():
            return False

        _purge_existing(session)
        now = datetime.utcnow()
        restaurant = Restaurant(
            name="Le Bistrot Demo",
            email="demo@projectempathy.test",
            phone_number="+33102030405",
            timezone="Europe/Paris",
            address="12 Rue de la Demo, 75000 Paris",
            twilio_phone_number="+33111222333",
        )

        starters = MenuCategory(name="Entrées", restaurant=restaurant)
        mains = MenuCategory(name="Plats", restaurant=restaurant)
        desserts = MenuCategory(name="Desserts", restaurant=restaurant)

        menu_items = [
            MenuItem(
                name="Soupe à l'oignon",
                description="Classique gratinée au fromage",
                price=Decimal("6.50"),
                category=starters,
                restaurant=restaurant,
            ),
            MenuItem(
                name="Boeuf bourguignon",
                description="Boeuf mijoté, légumes de saison",
                price=Decimal("17.90"),
                category=mains,
                restaurant=restaurant,
            ),
            MenuItem(
                name="Saumon grillé",
                description="Saumon Label Rouge, sauce beurre blanc",
                price=Decimal("19.40"),
                category=mains,
                restaurant=restaurant,
            ),
            MenuItem(
                name="Crème brûlée",
                description="Vanille bourbon, caramel croustillant",
                price=Decimal("7.20"),
                category=desserts,
                restaurant=restaurant,
            ),
        ]

        call_session = CallSession(
            call_sid="CA-demo-call",
            status="completed",
            transcript="Client: Bonjour, je voudrais commander deux boeufs bourguignons...",
            duration_seconds=420,
            restaurant=restaurant,
        )

        order = Order(
            restaurant=restaurant,
            call_session=call_session,
            customer_name="Claire Dupont",
            customer_phone="+33677889900",
            delivery_address="5 Rue Victor Hugo, Paris",
            status="confirmed",
        )
        order_items = [
            OrderItem(order=order, menu_item=menu_items[1], quantity=2, notes="Avec extra sauce"),
            OrderItem(order=order, menu_item=menu_items[3], quantity=1),
        ]
        order.total_amount = _calculate_total(order_items)

        reservation = Reservation(
            restaurant=restaurant,
            call_session=call_session,
            guest_name="Marc Lefèvre",
            guest_count=4,
            reservation_time=now + timedelta(days=2, hours=3),
            notes="Table près de la fenêtre",
        )

        plan = SubscriptionPlan(
            external_id="flexprice-standard",
            name="Standard",
            monthly_price=Decimal("149"),
            call_quota=1000,
            description="Forfait clé en main pour restaurants.",
        )
        subscription = Subscription(
            restaurant=restaurant,
            plan=plan,
            status="active",
            current_period_start=now - timedelta(days=5),
            current_period_end=now + timedelta(days=25),
            credits_remaining=420,
        )
        usage_records = [
            UsageRecord(
                subscription=subscription,
                metric="calls",
                amount=58,
                metadata_payload="{'period':'current'}",
            ),
            UsageRecord(
                subscription=subscription,
                metric="orders",
                amount=21,
                metadata_payload="{'period':'current'}",
            ),
        ]

        session.add_all([
            restaurant,
            plan,
            subscription,
            reservation,
            call_session,
            order,
            *order_items,
            *usage_records,
        ])
        session.commit()
        return True
    finally:
        if close_session:
            session.close()


def _calculate_total(items: Iterable[OrderItem]) -> Decimal:
    total = sum((item.menu_item.price * item.quantity for item in items), Decimal("0"))
    return total.quantize(Decimal("0.01"))


def _purge_existing(session: Session) -> None:
    if session.execute(select(Restaurant.id).limit(1)).first():
        for model in (
            UsageRecord,
            Subscription,
            SubscriptionPlan,
            Reservation,
            OrderItem,
            Order,
            CallSession,
            MenuItem,
            MenuCategory,
            Restaurant,
        ):
            session.query(model).delete()
        session.commit()


def _ensure_storage_dirs() -> None:
    settings = get_settings()
    for directory in (settings.storage.data_dir, settings.storage.transcripts_dir):
        Path(directory).mkdir(parents=True, exist_ok=True)


__all__ = ["create_schema", "seed_demo_data"]
