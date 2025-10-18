"""Translation routines for Project Empathy."""

from __future__ import annotations

from typing import List

import pandas as pd
from googletrans import Translator

from .config import AppConfig
from .db import read_table, upsert_json_rows
from .logging_utils import get_logger

LOGGER = get_logger("translate")


def translate_articles(config: AppConfig) -> pd.DataFrame:
    """Translate non-English articles into English."""

    db_path = config.storage.database_path
    clean_df = read_table(db_path, config.storage.clean_table)
    translator = Translator()
    updates: List[dict] = []
    for _, row in clean_df.iterrows():
        language = row.get("language", "en")
        if language in ("en", "en-us"):
            continue
        text = row.get("body_text", "")
        if not text:
            continue
        try:
            translated = translator.translate(text, dest="en")
            row["body_text"] = translated.text
            row["language"] = "en"
            row["was_translated"] = True
            updates.append(row.to_dict())
        except Exception as exc:  # pragma: no cover - network dependent
            LOGGER.error("Translation failed for %s: %s", row.get("url"), exc)
    if updates:
        upsert_json_rows(db_path, config.storage.clean_table, updates)
    LOGGER.info("Translated %d articles", len(updates))
    return pd.DataFrame(updates)
