"""Pydantic schemas for API responses and requests."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    is_available: bool = True
    category_id: Optional[int] = None


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0)
    is_available: Optional[bool] = None
    category_id: Optional[int] = None


class MenuItemRead(MenuItemBase):
    id: int
    restaurant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MenuCategoryBase(BaseModel):
    name: str


class MenuCategoryCreate(MenuCategoryBase):
    pass


class MenuCategoryRead(MenuCategoryBase):
    id: int
    restaurant_id: int
    items: List[MenuItemRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RestaurantBase(BaseModel):
    name: str
    email: str
    phone_number: Optional[str] = None
    timezone: str = "Europe/Paris"
    address: Optional[str] = None
    twilio_phone_number: Optional[str] = None


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    timezone: Optional[str] = None
    address: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    is_active: Optional[bool] = None


class RestaurantRead(RestaurantBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReceptionistProfileBase(BaseModel):
    display_name: str = Field(default="Empathy Concierge", max_length=128)
    greeting: str = Field(
        default="Bonjour et bienvenue chez nous ! Je suis votre réceptionniste virtuel, comment puis-je vous guider ?"
    )
    closing_remark: str = Field(
        default="Merci pour votre appel, nous avons hâte de vous accueillir. Excellente journée !"
    )
    tone: str = Field(default="Chaleureux et premium", max_length=64)
    personality: str = Field(
        default="Incarne un concierge cinq étoiles, empathique, proactif et orienté solution."
    )
    primary_language: str = Field(default="fr-FR", max_length=32)
    secondary_language: Optional[str] = Field(default=None, max_length=32)
    voice_name: str = Field(default="alice", max_length=64)
    upsell_phrases: List[str] = Field(default_factory=list)
    signature: Optional[str] = None
    custom_instructions: Optional[str] = None
    brand_primary_color: str = Field(default="#5B5CFF", max_length=16)
    brand_accent_color: str = Field(default="#21D4FD", max_length=16)
    brand_background_color: str = Field(default="#06071B", max_length=16)
    brand_text_color: str = Field(default="#F8FAFF", max_length=16)


class ReceptionistProfileRead(ReceptionistProfileBase):
    id: int
    restaurant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReceptionistProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=128)
    greeting: Optional[str] = None
    closing_remark: Optional[str] = None
    tone: Optional[str] = Field(default=None, max_length=64)
    personality: Optional[str] = None
    primary_language: Optional[str] = Field(default=None, max_length=32)
    secondary_language: Optional[str] = Field(default=None, max_length=32)
    voice_name: Optional[str] = Field(default=None, max_length=64)
    upsell_phrases: Optional[List[str]] = None
    signature: Optional[str] = None
    custom_instructions: Optional[str] = None
    brand_primary_color: Optional[str] = Field(default=None, max_length=16)
    brand_accent_color: Optional[str] = Field(default=None, max_length=16)
    brand_background_color: Optional[str] = Field(default=None, max_length=16)
    brand_text_color: Optional[str] = Field(default=None, max_length=16)


class ReceptionistPreview(BaseModel):
    system_prompt: str
    greeting: str
    closing_remark: str
    upsell_phrases: List[str] = Field(default_factory=list)
    tone: str
    voice_name: str
    languages: List[str] = Field(default_factory=list)
    signature: Optional[str] = None
    persona: Optional[str] = None
    custom_instructions: Optional[str] = None


class OrderItemBase(BaseModel):
    menu_item_id: int
    quantity: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemRead(OrderItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    menu_item: MenuItemRead

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    status: str = "pending"


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderRead(OrderBase):
    id: int
    restaurant_id: int
    call_session_id: Optional[int]
    total_amount: Decimal
    items: List[OrderItemRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: str


class ReservationBase(BaseModel):
    guest_name: str
    guest_count: int = Field(ge=1)
    reservation_time: datetime
    notes: Optional[str] = None


class ReservationCreate(ReservationBase):
    pass


class ReservationRead(ReservationBase):
    id: int
    restaurant_id: int
    call_session_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CallSessionBase(BaseModel):
    call_sid: str
    status: str = "in-progress"
    transcript: Optional[str] = None
    duration_seconds: Optional[int] = None


class CallSessionCreate(CallSessionBase):
    pass


class CallSessionRead(CallSessionBase):
    id: int
    restaurant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionPlanBase(BaseModel):
    external_id: str
    name: str
    monthly_price: Decimal
    call_quota: int = Field(default=100, ge=0)
    description: Optional[str] = None


class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass


class SubscriptionPlanRead(SubscriptionPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionBase(BaseModel):
    plan_id: int
    status: str = "active"
    current_period_start: datetime
    current_period_end: datetime
    credits_remaining: int = 0


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionRead(SubscriptionBase):
    id: int
    restaurant_id: int
    plan: SubscriptionPlanRead
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsageRecordBase(BaseModel):
    metric: str
    amount: int
    metadata: Optional[str] = Field(default=None, alias="metadata_payload")

    model_config = ConfigDict(populate_by_name=True)


class UsageRecordCreate(UsageRecordBase):
    pass


class UsageRecordRead(UsageRecordBase):
    id: int
    subscription_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DashboardStats(BaseModel):
    total_calls: int
    total_orders: int
    average_order_value: Decimal
    total_revenue: Decimal


class ApiTokenBase(BaseModel):
    name: str


class ApiTokenCreate(ApiTokenBase):
    pass


class ApiTokenRead(ApiTokenBase):
    id: int
    prefix: str
    revoked: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiTokenProvisioned(BaseModel):
    token: str
    metadata: ApiTokenRead

    model_config = ConfigDict(from_attributes=True)


class NotificationEndpointBase(BaseModel):
    name: str
    target_url: HttpUrl
    events: List[str] = Field(default_factory=lambda: ["orders.created", "orders.updated", "reservations.created"])
    secret: Optional[str] = Field(default=None, description="Optional shared secret used for HMAC signing")


class NotificationEndpointCreate(NotificationEndpointBase):
    pass


class NotificationEndpointUpdate(BaseModel):
    name: Optional[str] = None
    target_url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = Field(default=None, description="Optional shared secret used for HMAC signing")
    is_active: Optional[bool] = None


class NotificationEndpointRead(NotificationEndpointBase):
    id: int
    restaurant_id: int
    is_active: bool
    last_status_code: Optional[int] = None
    last_error: Optional[str] = None
    last_delivery_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationTestRequest(BaseModel):
    event_type: str = "orders.created"
    payload: dict = Field(default_factory=dict)


__all__ = [
    "RestaurantCreate",
    "RestaurantRead",
    "RestaurantUpdate",
    "MenuItemCreate",
    "MenuItemRead",
    "MenuItemUpdate",
    "MenuCategoryCreate",
    "MenuCategoryRead",
    "OrderCreate",
    "OrderRead",
    "OrderStatusUpdate",
    "OrderItemCreate",
    "ReservationCreate",
    "ReservationRead",
    "CallSessionCreate",
    "CallSessionRead",
    "SubscriptionPlanCreate",
    "SubscriptionPlanRead",
    "SubscriptionCreate",
    "SubscriptionRead",
    "UsageRecordCreate",
    "UsageRecordRead",
    "DashboardStats",
    "ApiTokenCreate",
    "ApiTokenRead",
    "ApiTokenProvisioned",
    "NotificationEndpointCreate",
    "NotificationEndpointRead",
    "NotificationEndpointUpdate",
    "NotificationTestRequest",
]
