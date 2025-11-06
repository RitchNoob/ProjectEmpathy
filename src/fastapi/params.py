"""Minimal form parameter support for the FastAPI shim."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class FormParam:
    default: Any = ...
    alias: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def Form(default: Any = ..., *, alias: Optional[str] = None, **extra: Any) -> FormParam:
    return FormParam(default=default, alias=alias, metadata=dict(extra))


@dataclass
class HeaderParam(FormParam):
    pass


def Header(default: Any = ..., *, alias: Optional[str] = None, **extra: Any) -> HeaderParam:
    return HeaderParam(default=default, alias=alias, metadata=dict(extra))


__all__ = ["Form", "FormParam", "Header", "HeaderParam"]
