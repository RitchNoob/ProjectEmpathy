"""Database models for the Project Empathy backend."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class TimestampMixin:
    """Add created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Restaurant(Base, TimestampMixin):
    """Restaurant subscribing to the SaaS."""

    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32))
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Paris", nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(512))
    twilio_phone_number: Mapped[Optional[str]] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    menu_items: Mapped[list["MenuItem"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    call_sessions: Mapped[list["CallSession"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    subscription: Mapped[Optional["Subscription"]] = relationship(
        back_populates="restaurant", uselist=False
    )
    api_tokens: Mapped[list["ApiToken"]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan"
    )
    notification_endpoints: Mapped[list["NotificationEndpoint"]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan"
    )
    receptionist_profile: Mapped[Optional["ReceptionistProfile"]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan", uselist=False
    )


class MenuCategory(Base, TimestampMixin):
    """Hierarchical grouping for menu items."""

    __tablename__ = "menu_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    restaurant: Mapped[Restaurant] = relationship(back_populates="menu_categories")
    items: Mapped[list["MenuItem"]] = relationship(back_populates="category", cascade="all, delete-orphan")


Restaurant.menu_categories = relationship(  # type: ignore[attr-defined]
    "MenuCategory", back_populates="restaurant", cascade="all, delete-orphan"
)


class MenuItem(Base, TimestampMixin):
    """Menu item available for ordering."""

    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("menu_categories.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    restaurant: Mapped[Restaurant] = relationship(back_populates="menu_items")
    category: Mapped[Optional[MenuCategory]] = relationship(back_populates="items")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="menu_item")


class CallSession(Base, TimestampMixin):
    """Persistent record for a phone call handled by the AI."""

    __tablename__ = "call_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False, index=True)
    call_sid: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), default="in-progress")
    transcript: Mapped[Optional[str]] = mapped_column(Text)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    restaurant: Mapped[Restaurant] = relationship(back_populates="call_sessions")
    orders: Mapped[list["Order"]] = relationship(back_populates="call_session")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="call_session")


class Order(Base, TimestampMixin):
    """Customer order captured by the AI receptionist."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False, index=True)
    call_session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("call_sessions.id"))
    customer_name: Mapped[Optional[str]] = mapped_column(String(255))
    customer_phone: Mapped[Optional[str]] = mapped_column(String(32))
    delivery_address: Mapped[Optional[str]] = mapped_column(Text)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(32), default="pending")

    restaurant: Mapped[Restaurant] = relationship(back_populates="orders")
    call_session: Mapped[Optional[CallSession]] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base, TimestampMixin):
    """Line item in an order."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    order: Mapped[Order] = relationship(back_populates="items")
    menu_item: Mapped[MenuItem] = relationship(back_populates="order_items")


class Reservation(Base, TimestampMixin):
    """Reservation captured via the conversational AI."""

    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False, index=True)
    call_session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("call_sessions.id"))
    guest_name: Mapped[str] = mapped_column(String(255), nullable=False)
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reservation_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    restaurant: Mapped[Restaurant] = relationship(back_populates="reservations")
    call_session: Mapped[Optional[CallSession]] = relationship(back_populates="reservations")


class SubscriptionPlan(Base, TimestampMixin):
    """Billing plan fetched from Flexprice or Stripe."""

    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    monthly_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    call_quota: Mapped[int] = mapped_column(Integer, default=100)
    description: Mapped[Optional[str]] = mapped_column(Text)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")


class Subscription(Base, TimestampMixin):
    """Active subscription for a restaurant."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), unique=True, nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active")
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    credits_remaining: Mapped[int] = mapped_column(Integer, default=0)

    restaurant: Mapped[Restaurant] = relationship(back_populates="subscription")
    plan: Mapped[SubscriptionPlan] = relationship(back_populates="subscriptions")
    usage_records: Mapped[list["UsageRecord"]] = relationship(back_populates="subscription", cascade="all, delete-orphan")


class UsageRecord(Base, TimestampMixin):
    """Track usage metrics for subscription enforcement."""

    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_payload: Mapped[Optional[str]] = mapped_column("metadata", Text)

    subscription: Mapped[Subscription] = relationship(back_populates="usage_records")


class ApiToken(Base, TimestampMixin):
    """API keys used by restaurateurs and integrations."""

    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    hashed_key: Mapped[str] = mapped_column(String(128), nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    restaurant: Mapped[Restaurant] = relationship(back_populates="api_tokens")


class NotificationEndpoint(Base, TimestampMixin):
    """Outbound notification targets for restaurant events."""

    __tablename__ = "notification_endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    target_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    events: Mapped[list[str]] = mapped_column(JSON, default=list)
    secret: Mapped[Optional[str]] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_status_code: Mapped[Optional[int]] = mapped_column(Integer)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    last_delivery_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    restaurant: Mapped[Restaurant] = relationship(back_populates="notification_endpoints")


class ReceptionistProfile(Base, TimestampMixin):
    """Persona and branding for the AI receptionist."""

    __tablename__ = "receptionist_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id"), nullable=False, unique=True, index=True
    )
    display_name: Mapped[str] = mapped_column(String(128), default="Empathy Concierge", nullable=False)
    greeting: Mapped[str] = mapped_column(
        Text,
        default="Bonjour et bienvenue chez nous ! Je suis votre réceptionniste virtuel, comment puis-je vous guider ?",
        nullable=False,
    )
    closing_remark: Mapped[str] = mapped_column(
        Text,
        default="Merci pour votre appel, nous avons hâte de vous accueillir. Excellente journée !",
        nullable=False,
    )
    tone: Mapped[str] = mapped_column(String(64), default="Chaleureux et premium", nullable=False)
    personality: Mapped[str] = mapped_column(
        Text,
        default="Incarne un concierge cinq étoiles, empathique, proactif et orienté solution.",
        nullable=False,
    )
    primary_language: Mapped[str] = mapped_column(String(32), default="fr-FR", nullable=False)
    secondary_language: Mapped[Optional[str]] = mapped_column(String(32))
    voice_name: Mapped[str] = mapped_column(String(64), default="alice", nullable=False)
    upsell_phrases: Mapped[list[str]] = mapped_column(JSON, default=list)
    signature: Mapped[Optional[str]] = mapped_column(
        Text,
        default="Votre concierge Project Empathy",
    )
    custom_instructions: Mapped[Optional[str]] = mapped_column(Text)
    brand_primary_color: Mapped[str] = mapped_column(String(16), default="#5B5CFF", nullable=False)
    brand_accent_color: Mapped[str] = mapped_column(String(16), default="#21D4FD", nullable=False)
    brand_background_color: Mapped[str] = mapped_column(String(16), default="#06071B", nullable=False)
    brand_text_color: Mapped[str] = mapped_column(String(16), default="#F8FAFF", nullable=False)

    restaurant: Mapped[Restaurant] = relationship(back_populates="receptionist_profile")


__all__ = [
    "Restaurant",
    "MenuCategory",
    "MenuItem",
    "Order",
    "OrderItem",
    "Reservation",
    "CallSession",
    "SubscriptionPlan",
    "Subscription",
    "UsageRecord",
    "ApiToken",
    "NotificationEndpoint",
    "ReceptionistProfile",
]
