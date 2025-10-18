"""Utility helpers for Project Empathy."""

from __future__ import annotations

import hashlib
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from os import getenv
from pathlib import Path
from typing import Dict, Generator, Iterable, Optional

import requests
from dotenv import load_dotenv

from .logging_utils import get_logger

LOGGER = get_logger("utils")


@dataclass
class RateLimiter:
    """Simple token bucket rate limiter."""

    interval: float
    last_call: float = 0.0

    def wait(self) -> None:
        """Sleep until next request is allowed."""

        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.interval:
            delay = self.interval - elapsed
            LOGGER.debug("Rate limiter sleeping for %.2f seconds", delay)
            time.sleep(delay)
        self.last_call = time.time()


def hash_text(text: str) -> str:
    """Return SHA256 hash of text."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_directory(path: Path) -> None:
    """Ensure directory exists."""

    path.mkdir(parents=True, exist_ok=True)


@contextmanager
def request_context(session: Optional[requests.Session] = None) -> Generator[requests.Session, None, None]:
    """Context manager for requests session."""

    created_session = session is None
    session = session or requests.Session()
    try:
        yield session
    finally:
        if created_session:
            session.close()


def load_environment(dotenv_path: Optional[Path] = None) -> Dict[str, str]:
    """Load environment variables from .env file."""

    load_dotenv(dotenv_path)
    return {
        "NEWSAPI_KEY": getenv("NEWSAPI_KEY", ""),
        "USER_AGENT": getenv("USER_AGENT", "ProjectEmpathyBot/0.1"),
        "REQUESTS_PER_MINUTE": getenv("REQUESTS_PER_MINUTE", "15"),
    }


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO-like datetime strings."""

    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def chunked(iterable: Iterable, size: int) -> Generator[list, None, None]:
    """Yield chunks from iterable."""

    chunk: list = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
