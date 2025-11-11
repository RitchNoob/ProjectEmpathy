"""Very small test client compatible with the FastAPI interface used in tests."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from .applications import FastAPI
from .dependencies import Dependency
from .exceptions import HTTPException
from .params import FormParam, HeaderParam
from .status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR


@dataclass
class TestResponse:
    status_code: int
    content: Any

    def json(self) -> Any:
        return self.content


class TestClient:
    """Very small HTTP-less client that calls route handlers directly."""

    def __init__(self, app: FastAPI):
        self.app = app

    def __enter__(self) -> "TestClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def get(
        self,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, Any]] = None,
    ) -> TestResponse:
        return self._request("GET", url, params=params, headers=headers)

    def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        headers: Optional[Mapping[str, Any]] = None,
    ) -> TestResponse:
        return self._request("POST", url, json=json, data=data, headers=headers)

    def patch(
        self,
        url: str,
        *,
        json: Any | None = None,
        headers: Optional[Mapping[str, Any]] = None,
    ) -> TestResponse:
        return self._request("PATCH", url, json=json, headers=headers)

    def delete(
        self,
        url: str,
        *,
        headers: Optional[Mapping[str, Any]] = None,
    ) -> TestResponse:
        return self._request("DELETE", url, headers=headers)

    def _request(
        self,
        method: str,
        url: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, Any] | None = None,
    ) -> TestResponse:
        method = method.upper()
        path = url.split("?", 1)[0]
        match = self.app._match(method, path)
        if match is None:
            return TestResponse(status_code=HTTP_404_NOT_FOUND, content={"detail": "Not Found"})

        route, path_params = match
        cleanups: List[Any] = []
        error: Optional[BaseException] = None
        should_raise = False
        dependency_cache: Dict[Any, Tuple[Any, Optional[Any]]] = {}
        try:
            kwargs = self._build_kwargs(
                route.endpoint,
                path_params,
                json=json,
                data=data,
                params=params,
                headers=headers,
                dependency_cache=dependency_cache,
                cleanups=cleanups,
            )
            result = route.endpoint(**kwargs)
            status_code = route.status_code or 200
            if status_code == 204:
                content = None
            else:
                content = _serialize_response(route.response_model, result)
        except HTTPException as exc:
            status_code = exc.status_code
            content = {"detail": exc.detail}
            error = exc
            should_raise = False
        except Exception as exc:  # pragma: no cover - defensive default
            if isinstance(exc, AssertionError):
                raise
            error = exc
            should_raise = True
        finally:
            for cleanup in reversed(cleanups):
                cleanup(error)
        if error and should_raise:
            raise error
        return TestResponse(status_code=status_code, content=content)

    def _build_kwargs(
        self,
        endpoint: Any,
        path_params: Mapping[str, str],
        *,
        json: Any | None,
        data: Any | None,
        params: Mapping[str, Any] | None,
        headers: Mapping[str, Any] | None,
        dependency_cache: Dict[Any, Tuple[Any, Optional[Any]]],
        cleanups: List[Any],
    ) -> Dict[str, Any]:
        sig = inspect.signature(endpoint)
        type_hints = get_type_hints(endpoint)
        values: Dict[str, Any] = {}
        body_consumed = False
        for name, param in sig.parameters.items():
            default = param.default
            annotation = type_hints.get(name, param.annotation)
            if isinstance(default, Dependency):
                value, cleanup = _resolve_dependency(
                    self,
                    default.dependency,
                    path_params,
                    json=json,
                    data=data,
                    params=params,
                    headers=headers,
                    dependency_cache=dependency_cache,
                    cleanups=cleanups,
                )
                values[name] = value
                if cleanup is not None:
                    cleanups.append(cleanup)
                continue

            if name in path_params:
                values[name] = _convert_type(path_params[name], annotation)
                continue

            if isinstance(default, HeaderParam):
                header_name = default.alias or name
                header_payload = headers or {}
                if header_name in header_payload:
                    values[name] = _convert_type(header_payload[header_name], annotation)
                elif default.default is ...:
                    raise ValueError(f"Missing header: {header_name}")
                else:
                    values[name] = default.default
                continue

            if isinstance(default, FormParam):
                field_name = default.alias or name
                form_payload = data or {}
                if isinstance(form_payload, Mapping) and field_name in form_payload:
                    values[name] = _convert_type(form_payload[field_name], annotation)
                elif default.default is ...:
                    raise ValueError(f"Missing form field: {field_name}")
                else:
                    values[name] = default.default
                continue

            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            if not body_consumed and json is not None:
                values[name] = _coerce_body(json, annotation)
                body_consumed = True
                continue

            if params and name in params:
                values[name] = _convert_type(params[name], annotation)
                continue

            if default is not inspect._empty:
                values[name] = default
                continue

            raise ValueError(f"Unable to resolve value for parameter '{name}'")
        return values


def _resolve_dependency(
    client: "TestClient",
    func: Any,
    path_params: Mapping[str, str],
    *,
    json: Any | None,
    data: Any | None,
    params: Mapping[str, Any] | None,
    headers: Mapping[str, Any] | None,
    dependency_cache: Dict[Any, Tuple[Any, Optional[Any]]],
    cleanups: List[Any],
) -> Tuple[Any, Optional[Any]]:
    if func in dependency_cache:
        cached_value, cached_cleanup = dependency_cache[func]
        return cached_value, None

    kwargs = client._build_kwargs(
        func,
        path_params,
        json=json,
        data=data,
        params=params,
        headers=headers,
        dependency_cache=dependency_cache,
        cleanups=cleanups,
    )
    value = func(**kwargs)
    if inspect.isgenerator(value):
        generator = value
        try:
            provided = next(generator)
        except StopIteration as exc:  # pragma: no cover - defensive
            raise RuntimeError("Dependency generator did not yield a value") from exc

        def cleanup(error: Optional[BaseException]) -> None:
            try:
                if error:
                    generator.throw(error)
                else:
                    next(generator)
            except StopIteration:
                return
            except BaseException:
                return

        dependency_cache[func] = (provided, cleanup)
        return provided, cleanup
    dependency_cache[func] = (value, None)
    return value, None


def _convert_type(value: Any, annotation: Any) -> Any:
    if annotation is inspect.Signature.empty or annotation is Any:
        return value
    origin = get_origin(annotation)
    if origin is Union:
        for arg in get_args(annotation):
            try:
                return _convert_type(value, arg)
            except Exception:
                continue
        return value
    if annotation in (str, int, float, bool):
        return annotation(value)
    return value


def _coerce_body(payload: Any, annotation: Any) -> Any:
    if annotation is inspect.Signature.empty or annotation is Any:
        return payload
    if hasattr(annotation, "model_validate"):
        return annotation.model_validate(payload)
    return _convert_type(payload, annotation)


def _serialize_response(model: Any | None, value: Any) -> Any:
    if model is None:
        return _default_serialize(value)
    origin = get_origin(model)
    if origin in (list, List):
        inner = get_args(model)[0]
        return [_serialize_response(inner, item) for item in (value or [])]
    if origin is Union:
        for arg in get_args(model):
            try:
                return _serialize_response(arg, value)
            except Exception:
                continue
    if inspect.isclass(model) and issubclass(model, BaseModel):
        instance = model.model_validate(value)
        return instance.model_dump(mode="json")
    return _default_serialize(value)


def _default_serialize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        return [_default_serialize(item) for item in value]
    if isinstance(value, Mapping):
        return {key: _default_serialize(val) for key, val in value.items()}
    if hasattr(value, "__dict__"):
        return {
            key: _default_serialize(val)
            for key, val in vars(value).items()
            if not key.startswith("_")
        }
    return value


__all__ = ["TestClient", "TestResponse"]
