"""Placeholder CORS middleware for the FastAPI shim."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass
class CORSMiddleware:
    app: object
    allow_origins: Sequence[str] | Iterable[str]
    allow_credentials: bool = False
    allow_methods: Sequence[str] | Iterable[str] = ()
    allow_headers: Sequence[str] | Iterable[str] = ()


__all__ = ["CORSMiddleware"]
