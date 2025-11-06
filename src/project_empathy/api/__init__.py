"""API routers for Project Empathy."""

from __future__ import annotations

from fastapi import APIRouter

from . import orders, restaurants, subscriptions, twilio, dashboard, menu, reservations, calls


def get_api_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(restaurants.router)
    router.include_router(menu.router)
    router.include_router(orders.router)
    router.include_router(reservations.router)
    router.include_router(calls.router)
    router.include_router(subscriptions.router)
    router.include_router(dashboard.router)
    router.include_router(twilio.router)
    return router


__all__ = ["get_api_router"]
