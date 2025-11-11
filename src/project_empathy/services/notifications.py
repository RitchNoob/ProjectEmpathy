"""Webhook notification delivery helpers."""

from __future__ import annotations

from datetime import datetime
import hashlib
import hmac
import json
from functools import lru_cache
from typing import Iterable

import httpx
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import NotificationEndpoint


class NotificationDispatcher:
    """Deliver webhook notifications to subscribed restaurant endpoints."""

    def __init__(self, client: httpx.Client | None = None, timeout: int | None = None) -> None:
        settings = get_settings()
        self._timeout = timeout or settings.notifications.delivery_timeout
        self._client = client or httpx.Client(timeout=self._timeout)
        self._signature_header = settings.notifications.signature_header
        self._event_header = settings.notifications.event_header

    def dispatch(
        self,
        session: Session,
        endpoints: Iterable[NotificationEndpoint],
        event_type: str,
        payload: dict,
    ) -> None:
        """Send the payload to each endpoint that subscribes to the event."""

        body = json.dumps({"event": event_type, "data": payload, "sent_at": datetime.utcnow().isoformat()})
        for endpoint in endpoints:
            if not endpoint.is_active:
                continue
            if endpoint.events and event_type not in endpoint.events:
                continue

            headers = {
                "Content-Type": "application/json",
                self._event_header: event_type,
            }

            if endpoint.secret:
                signature = hmac.new(endpoint.secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()
                headers[self._signature_header] = signature

            status_code: int | None = None
            error: str | None = None
            try:
                response = self._client.post(endpoint.target_url, content=body, headers=headers)
                status_code = response.status_code
                if response.status_code >= 400:
                    error = response.text[:512]
            except Exception as exc:  # pragma: no cover - network errors are environment specific
                error = str(exc)

            endpoint.last_status_code = status_code
            endpoint.last_error = error
            endpoint.last_delivery_at = datetime.utcnow()
            session.add(endpoint)

        session.flush()


@lru_cache
def get_notification_dispatcher() -> NotificationDispatcher:
    """Return a cached notification dispatcher instance."""

    return NotificationDispatcher()


def dispatch_notification(session: Session, restaurant_id: int, event_type: str, payload: dict) -> None:
    """Load endpoints and deliver the notification payload."""

    settings = get_settings()
    if not settings.notifications.enabled:
        return

    endpoints = (
        session.query(NotificationEndpoint)
        .filter(NotificationEndpoint.restaurant_id == restaurant_id)
        .all()
    )
    if not endpoints:
        return

    dispatcher = get_notification_dispatcher()
    dispatcher.dispatch(session, endpoints, event_type, payload)


__all__ = ["NotificationDispatcher", "dispatch_notification", "get_notification_dispatcher"]
