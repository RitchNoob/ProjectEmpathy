"""Exception types for the minimal FastAPI shim."""

from __future__ import annotations

from typing import Any


class HTTPException(Exception):
    """Mimic fastapi.HTTPException for tests."""

    def __init__(self, status_code: int, detail: Any | None = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


__all__ = ["HTTPException"]
