"""Database session management for the Project Empathy backend."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy.engine import Engine

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import get_settings


Base = declarative_base()


@lru_cache(maxsize=1)
def _create_engine(url: str, echo: bool) -> Engine:
    return create_engine(url, echo=echo, future=True)


def get_engine():
    """Lazy engine creation to support testing overrides."""

    settings = get_settings()
    return _create_engine(settings.database.url, settings.database.echo)


SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, class_=Session)


def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - rollback is critical even if not triggered in tests
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine_cache() -> None:
    """Clear the cached SQLAlchemy engine (used in tests and CLI tooling)."""

    _create_engine.cache_clear()


__all__ = ["Base", "get_session", "SessionLocal", "get_engine", "reset_engine_cache"]
