"""Minimal pydantic-settings compatibility layer for the tests."""

from __future__ import annotations

import os
from typing import Any, Dict

from pydantic import BaseModel


def SettingsConfigDict(**kwargs: Any) -> Dict[str, Any]:
    return dict(kwargs)


class BaseSettings(BaseModel):
    """Simplified BaseSettings that pulls values from environment variables."""

    model_config: Dict[str, Any] = SettingsConfigDict()

    def __init__(self, **data: Any) -> None:
        env_values = self._build_env_data()
        env_values.update(data)
        super().__init__(**env_values)

    @classmethod
    def _build_env_data(cls) -> Dict[str, Any]:
        config = getattr(cls, "model_config", {}) or {}
        prefix = config.get("env_prefix", "") or ""
        delimiter = config.get("env_nested_delimiter", "__") or "__"
        values: Dict[str, Any] = {}
        for key, raw_value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            stripped = key[len(prefix):] if prefix else key
            if not stripped:
                continue
            parts = [part.lower() for part in stripped.split(delimiter) if part]
            if not parts:
                continue
            target = values
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = raw_value
        return values


__all__ = ["BaseSettings", "SettingsConfigDict"]
