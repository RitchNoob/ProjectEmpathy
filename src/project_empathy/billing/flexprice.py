"""Client for interacting with the Flexprice subscription API."""

from __future__ import annotations

from typing import Any, Dict, Iterable

import httpx

from ..config import get_settings


class FlexpriceClient:
    """Minimal Flexprice API client used for plan and subscription management."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.flexprice.base_url
        self.api_key = api_key or settings.flexprice.api_key
        self._client = httpx.Client(base_url=self.base_url, headers=self._headers)

    @property
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def list_plans(self) -> Iterable[Dict[str, Any]]:
        response = self._client.get("/plans")
        response.raise_for_status()
        return response.json()

    def create_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self._client.post("/plans", json=payload)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()


__all__ = ["FlexpriceClient"]
