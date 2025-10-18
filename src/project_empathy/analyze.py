"""Analysis routines for Project Empathy."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob

from .config import AppConfig
from .db import read_table, upsert_json_rows
from .logging_utils import get_logger

LOGGER = get_logger("analyze")

CATEGORIES = {
    "education": ["school", "university", "college", "student"],
    "discipline": ["bully", "bullying", "discipline", "expel"],
    "cyberbullying": ["online", "cyber", "social media"],
    "mental_health": ["mental", "depression", "suicide"],
}


def analyze_articles(config: AppConfig) -> Dict[str, pd.DataFrame]:
    """Perform TF-IDF, co-occurrence, and sentiment analysis."""

    db_path = config.storage.database_path
    clean_df = read_table(db_path, config.storage.clean_table)
    if clean_df.empty:
        LOGGER.warning("No cleaned articles to analyze")
        return {}
    clean_df["published_at"] = pd.to_datetime(clean_df["published_at"], errors="coerce")
    if "was_translated" in clean_df.columns:
        clean_df["was_translated"] = clean_df["was_translated"].astype(bool)
    tfidf_df = _tfidf(clean_df, config.pipeline.tfidf_top_k)
    cooccurrence_df = _cooccurrence(clean_df)
    sentiment_df = _sentiment(clean_df, config.pipeline.sentiment_time_window)
    analyzed_rows = _merge_analysis(clean_df, tfidf_df, sentiment_df)
    upsert_json_rows(db_path, config.storage.analyzed_table, analyzed_rows.to_dict(orient="records"))
    return {
        "tfidf": tfidf_df,
        "cooccurrence": cooccurrence_df,
        "sentiment": sentiment_df,
        "articles": analyzed_rows,
    }


def _tfidf(clean_df: pd.DataFrame, top_k: int) -> pd.DataFrame:
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(clean_df["body_text"].tolist())
    feature_names = vectorizer.get_feature_names_out()
    top_terms = []
    for idx, row in enumerate(matrix):
        data = row.toarray()[0]
        top_indices = data.argsort()[::-1][:top_k]
        top_terms.append(
            {
                "url": clean_df.iloc[idx]["url"],
                "keywords": [feature_names[i] for i in top_indices if data[i] > 0],
            }
        )
    return pd.DataFrame(top_terms)


def _cooccurrence(clean_df: pd.DataFrame) -> pd.DataFrame:
    counts = []
    for _, row in clean_df.iterrows():
        text = row["body_text"].lower()
        categories = [name for name, keywords in CATEGORIES.items() if any(keyword in text for keyword in keywords)]
        counts.append({"url": row["url"], "categories": categories})
    return pd.DataFrame(counts)


def _sentiment(clean_df: pd.DataFrame, window: str) -> pd.DataFrame:
    sentiments = []
    for _, row in clean_df.iterrows():
        text = row["body_text"]
        sentiment = TextBlob(text).sentiment.polarity
        published_at = _parse_datetime(row.get("published_at"))
        sentiments.append(
            {
                "url": row["url"],
                "sentiment": sentiment,
                "published_at": published_at,
            }
        )
    sentiment_df = pd.DataFrame(sentiments)
    sentiment_df["published_at"] = pd.to_datetime(sentiment_df["published_at"])
    daily = sentiment_df.set_index("published_at").resample(window).mean(numeric_only=True).reset_index()
    return daily


def _merge_analysis(clean_df: pd.DataFrame, tfidf_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> pd.DataFrame:
    merged = clean_df.merge(tfidf_df, on="url", how="left").merge(
        sentiment_df.rename(columns={"sentiment": "article_sentiment"}),
        on="published_at",
        how="left",
    )
    merged["article_sentiment"].fillna(0.0, inplace=True)
    merged["keywords"] = merged["keywords"].apply(lambda x: x if isinstance(x, list) else [])
    merged["was_translated"] = merged["was_translated"].astype(bool)
    merged["categories"] = merged["body_text"].apply(_categorize_text)
    return merged


def _categorize_text(text: str) -> List[str]:
    text_lower = text.lower()
    return [name for name, keywords in CATEGORIES.items() if any(keyword in text_lower for keyword in keywords)]


def _parse_datetime(value) -> datetime | None:  # type: ignore[override]
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None
