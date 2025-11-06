"""Database session management for the Project Empathy backend."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import get_settings


Base = declarative_base()


def _create_engine():
    settings = get_settings()
    return create_engine(settings.database.url, echo=settings.database.echo, future=True)


def get_engine():
    """Lazy engine creation to support testing overrides."""

    return _create_engine()


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


__all__ = ["Base", "get_session", "SessionLocal", "get_engine"]
