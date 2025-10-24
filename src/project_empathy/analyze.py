"""Analysis routines for Project Empathy."""

from __future__ import annotations

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
    clean_df = clean_df.copy()
    clean_df["published_at"] = pd.to_datetime(clean_df["published_at"], errors="coerce")
    window = config.pipeline.sentiment_time_window
    clean_df["published_at_window"] = clean_df["published_at"].dt.floor(window)
    if "was_translated" in clean_df.columns:
        clean_df["was_translated"] = clean_df["was_translated"].astype(bool)
    tfidf_df = _tfidf(clean_df, config.pipeline.tfidf_top_k)
    cooccurrence_df = _cooccurrence(clean_df)
    article_sentiment_df, aggregated_sentiment_df = _sentiment(clean_df, window)
    analyzed_rows = _merge_analysis(clean_df, tfidf_df, article_sentiment_df)

    db_rows = analyzed_rows.rename(columns={"article_sentiment": "sentiment"}).copy()
    allowed_columns = {
        "url",
        "source_domain",
        "title",
        "body_text",
        "published_at",
        "language",
        "was_translated",
        "sentiment",
        "keywords",
        "categories",
        "created_at",
    }
    existing_columns = [column for column in db_rows.columns if column in allowed_columns]
    upsert_json_rows(db_path, config.storage.analyzed_table, db_rows[existing_columns].to_dict(orient="records"))
    return {
        "tfidf": tfidf_df,
        "cooccurrence": cooccurrence_df,
        "sentiment": aggregated_sentiment_df,
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


def _sentiment(clean_df: pd.DataFrame, window: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    window_col = "published_at_window"
    working_df = clean_df.copy()
    working_df["published_at"] = pd.to_datetime(working_df["published_at"], errors="coerce")
    if window_col not in working_df.columns:
        working_df[window_col] = working_df["published_at"].dt.floor(window)

    sentiments: List[Dict[str, object]] = []
    for row in working_df.itertuples(index=False):
        text = getattr(row, "body_text", "") or ""
        sentiment = TextBlob(text).sentiment.polarity
        sentiments.append(
            {
                "url": getattr(row, "url"),
                "sentiment": sentiment,
                "published_at": getattr(row, "published_at"),
                window_col: getattr(row, window_col),
            }
        )

    article_sentiment_df = pd.DataFrame(sentiments)
    if article_sentiment_df.empty:
        empty_columns = ["published_at", "sentiment", window_col]
        return article_sentiment_df, pd.DataFrame(columns=empty_columns)

    article_sentiment_df["published_at"] = pd.to_datetime(article_sentiment_df["published_at"])
    article_sentiment_df[window_col] = pd.to_datetime(article_sentiment_df[window_col])

    aggregated_sentiment_df = (
        article_sentiment_df.groupby(window_col, as_index=False)["sentiment"].mean()
        .rename(columns={window_col: "published_at"})
    )
    aggregated_sentiment_df["published_at"] = pd.to_datetime(aggregated_sentiment_df["published_at"])
    aggregated_sentiment_df["sentiment"] = aggregated_sentiment_df["sentiment"].astype(float)
    aggregated_sentiment_df[window_col] = aggregated_sentiment_df["published_at"]

    return article_sentiment_df, aggregated_sentiment_df


def _merge_analysis(
    clean_df: pd.DataFrame, tfidf_df: pd.DataFrame, sentiment_df: pd.DataFrame
) -> pd.DataFrame:
    sentiment_merge = (
        sentiment_df.rename(columns={"sentiment": "article_sentiment"})[
            ["url", "published_at_window", "article_sentiment"]
        ]
        .drop_duplicates(subset=["url", "published_at_window"])
    )
    merged = clean_df.merge(tfidf_df, on="url", how="left").merge(
        sentiment_merge,
        on=["url", "published_at_window"],
        how="left",
    )
    merged["article_sentiment"] = merged["article_sentiment"].fillna(0.0)
    merged["keywords"] = merged["keywords"].apply(lambda x: x if isinstance(x, list) else [])
    merged["was_translated"] = merged["was_translated"].astype(bool)
    merged["categories"] = merged["body_text"].apply(_categorize_text)
    return merged


def _categorize_text(text: str) -> List[str]:
    text_lower = text.lower()
    return [name for name, keywords in CATEGORIES.items() if any(keyword in text_lower for keyword in keywords)]


