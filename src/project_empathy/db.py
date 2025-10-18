"""Database utilities for Project Empathy."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import pandas as pd

from .logging_utils import get_logger

LOGGER = get_logger("db")


def init_db(path: Path) -> None:
    """Initialize database with necessary tables."""

    LOGGER.info("Initializing database at %s", path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS articles_raw (
                url TEXT PRIMARY KEY,
                source_domain TEXT,
                title TEXT,
                body_text TEXT,
                published_at TEXT,
                language TEXT,
                created_at TEXT,
                content_hash TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS articles_clean (
                url TEXT PRIMARY KEY,
                source_domain TEXT,
                title TEXT,
                body_text TEXT,
                published_at TEXT,
                language TEXT,
                was_translated INTEGER,
                created_at TEXT,
                content_hash TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS articles_analyzed (
                url TEXT PRIMARY KEY,
                source_domain TEXT,
                title TEXT,
                body_text TEXT,
                published_at TEXT,
                language TEXT,
                was_translated INTEGER,
                sentiment REAL,
                keywords TEXT,
                categories TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()


@contextmanager
def connect(path: Path) -> Iterator[sqlite3.Connection]:
    """Context manager for SQLite connection."""

    conn = sqlite3.connect(path)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def upsert_dataframe(path: Path, table: str, frame: pd.DataFrame) -> None:
    """Upsert dataframe into table based on URL primary key."""

    LOGGER.info("Upserting %d records into %s", len(frame), table)
    with connect(path) as conn:
        frame.to_sql(table, conn, if_exists="append", index=False)


def read_table(path: Path, table: str) -> pd.DataFrame:
    """Read table into dataframe."""

    with connect(path) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)


def upsert_json_rows(path: Path, table: str, rows: Iterable[dict]) -> None:
    """Upsert rows using INSERT OR REPLACE."""

    with connect(path) as conn:
        cursor = conn.cursor()
        for row in rows:
            keys = list(row.keys())
            columns = ",".join(keys)
            placeholders = ":" + ",:".join(keys)
            cursor.execute(
                f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})",
                {key: _serialize_value(row[key]) for key in keys},
            )


def _serialize_value(value):  # type: ignore[no-untyped-def]
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # pragma: no cover - best effort serialization
            return str(value)
    return value


def fetch_many(path: Path, table: str, columns: Sequence[str]) -> Iterable[dict]:
    """Fetch dictionaries for given columns."""

    with connect(path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT {','.join(columns)} FROM {table}")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
