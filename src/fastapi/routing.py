"""Simplified routing implementation used in the FastAPI shim."""

from __future__ import annotations

from dataclasses import dataclass, replace
from inspect import Parameter, Signature, isgeneratorfunction, signature
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from .dependencies import Dependency


@dataclass
class Route:
    path: str
    methods: Tuple[str, ...]
    endpoint: Callable[..., Any]
    response_model: Any | None = None
    status_code: int | None = None

    def normalized_segments(self) -> Tuple[str, ...]:
        return tuple(seg for seg in self.path.strip("/").split("/") if seg)

    def with_prefix(self, prefix: str) -> "Route":
        if not prefix:
            return self
        combined = _join_paths(prefix, self.path)
        return replace(self, path=combined)


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path or "/"


def _join_paths(prefix: str, path: str) -> str:
    if not prefix:
        return _normalize_path(path)
    if not path:
        return _normalize_path(prefix)
    return _normalize_path("/".join(
        segment for segment in (prefix.strip("/"), path.strip("/")) if segment
    ))


class APIRouter:
    """Collect routes and nested routers."""

    def __init__(self, *, prefix: str = "", tags: Optional[Iterable[str]] = None):
        self.prefix = _normalize_path(prefix) if prefix else ""
        self.tags = list(tags or [])
        self.routes: List[Route] = []

    # decorator helpers -------------------------------------------------
    def get(self, path: str, *, response_model: Any | None = None, status_code: int | None = None, **extra: Any):
        return self.route(
            path, methods=("GET",), response_model=response_model, status_code=status_code, **extra
        )

    def post(self, path: str, *, response_model: Any | None = None, status_code: int | None = None, **extra: Any):
        return self.route(
            path, methods=("POST",), response_model=response_model, status_code=status_code, **extra
        )

    def patch(self, path: str, *, response_model: Any | None = None, status_code: int | None = None, **extra: Any):
        return self.route(
            path, methods=("PATCH",), response_model=response_model, status_code=status_code, **extra
        )

    def delete(self, path: str, *, response_model: Any | None = None, status_code: int | None = None, **extra: Any):
        return self.route(
            path, methods=("DELETE",), response_model=response_model, status_code=status_code, **extra
        )

    def route(
        self,
        path: str,
        *,
        methods: Tuple[str, ...],
        response_model: Any | None = None,
        status_code: int | None = None,
        **_ignored: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        full_path = _join_paths(self.prefix, path)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(
                Route(path=full_path, methods=tuple(methods), endpoint=func, response_model=response_model, status_code=status_code)
            )
            return func

        return decorator

    def include_router(self, router: "APIRouter") -> None:
        for route in router.routes:
            self.routes.append(route.with_prefix(self.prefix))


__all__ = ["APIRouter", "Route"]
