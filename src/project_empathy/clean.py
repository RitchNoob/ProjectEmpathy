"""Cleaning routines for Project Empathy."""

from __future__ import annotations

import re
from datetime import datetime
from typing import List

import pandas as pd

from .config import AppConfig
from .db import read_table, upsert_json_rows
from .logging_utils import get_logger
from .models import ArticleClean
from .utils import hash_text

LOGGER = get_logger("clean")

BOILERPLATE_PATTERNS = [
    re.compile(r"This article was first published", re.I),
    re.compile(r"All rights reserved", re.I),
]


def clean_articles(config: AppConfig) -> pd.DataFrame:
    """Clean raw articles and store results."""

    db_path = config.storage.database_path
    raw_df = read_table(db_path, config.storage.raw_table)
    LOGGER.info("Loaded %d raw articles", len(raw_df))
    cleaned_rows: List[dict] = []
    for _, row in raw_df.iterrows():
        body = row.get("body_text") or ""
        body = _strip_boilerplate(body)
        body = _normalize_whitespace(body)
        if len(body) < config.pipeline.min_article_length:
            LOGGER.debug("Skipping short article: %s", row.get("url"))
            continue
        title = (row.get("title") or "Untitled").strip()
        language = (row.get("language") or "en").lower()
        content_hash = hash_text(body)
        raw_translated = row.get("was_translated", 0)
        was_translated = bool(raw_translated) if pd.notna(raw_translated) else False
        cleaned = ArticleClean(
            url=row.get("url"),
            source_domain=row.get("source_domain"),
            title=title,
            body_text=body,
            published_at=_parse_datetime(row.get("published_at")),
            language=language,
            was_translated=was_translated,
            content_hash=content_hash,
        )
        cleaned_rows.append(_to_serializable(cleaned))
    if cleaned_rows:
        upsert_json_rows(db_path, config.storage.clean_table, cleaned_rows)
    LOGGER.info("Stored %d cleaned articles", len(cleaned_rows))
    return pd.DataFrame(cleaned_rows)


def _strip_boilerplate(text: str) -> str:
    for pattern in BOILERPLATE_PATTERNS:
        text = pattern.sub("", text)
    return text


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _parse_datetime(value) -> datetime | None:  # type: ignore[override]
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _to_serializable(article: ArticleClean) -> dict:
    payload = article.dict()
    if article.published_at:
        payload["published_at"] = article.published_at.isoformat()
    return payload
