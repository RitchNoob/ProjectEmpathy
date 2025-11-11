"""Dependency helpers for the FastAPI shim."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Dependency:
    """Container storing the dependency callable."""

    dependency: Callable[..., Any]


def Depends(dependency: Callable[..., Any]) -> Dependency:
    """Return a dependency marker mimicking fastapi.Depends."""

    return Dependency(dependency)


__all__ = ["Depends", "Dependency"]
