"""Application object for the lightweight FastAPI shim."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

from .routing import APIRouter, Route


@dataclass
class RegisteredMiddleware:
    middleware_class: type
    options: Dict[str, Any]


class FastAPI:
    """Minimal FastAPI compatible surface for unit tests."""

    def __init__(self, *, title: str | None = None, version: str | None = None, debug: bool = False):
        self.title = title
        self.version = version
        self.debug = debug
        self.routes: List[Route] = []
        self.middleware: List[RegisteredMiddleware] = []

    def add_middleware(self, middleware_class: type, **options: Any) -> None:
        self.middleware.append(RegisteredMiddleware(middleware_class=middleware_class, options=dict(options)))

    def include_router(self, router: APIRouter) -> None:
        self.routes.extend(router.routes)

    def add_api_route(
        self,
        path: str,
        endpoint: Any,
        *,
        methods: Iterable[str],
        response_model: Any | None = None,
        status_code: int | None = None,
    ) -> None:
        router = APIRouter(prefix="")
        router.route(path, methods=tuple(methods), response_model=response_model, status_code=status_code)(endpoint)
        self.include_router(router)

    def _match(self, method: str, path: str) -> Tuple[Route, Dict[str, str]] | None:
        cleaned_segments = tuple(seg for seg in path.strip("/").split("/") if seg)
        for route in self.routes:
            if method not in route.methods:
                continue
            match = _match_segments(route.normalized_segments(), cleaned_segments)
            if match is not None:
                return route, match
        return None


def _match_segments(pattern: Tuple[str, ...], value: Tuple[str, ...]) -> Dict[str, str] | None:
    if len(pattern) != len(value):
        return None
    params: Dict[str, str] = {}
    for pattern_seg, value_seg in zip(pattern, value):
        if pattern_seg.startswith("{") and pattern_seg.endswith("}"):
            params[pattern_seg[1:-1]] = value_seg
        elif pattern_seg != value_seg:
            return None
    return params


__all__ = ["FastAPI", "APIRouter"]
