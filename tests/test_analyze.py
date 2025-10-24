from pathlib import Path

import pandas as pd
import pytest
from textblob import TextBlob

pytest.importorskip("pandas")
pytest.importorskip("sklearn")
pytest.importorskip("textblob")

from project_empathy.analyze import analyze_articles
from project_empathy.config import AppConfig, NewsConfig
from project_empathy.db import init_db, upsert_json_rows


@pytest.fixture()
def analyzed_config(tmp_path: Path) -> AppConfig:
    db_path = tmp_path / "empathy.db"
    init_db(db_path)
    config = AppConfig(
        storage={
            "database_path": db_path,
            "raw_table": "articles_raw",
            "clean_table": "articles_clean",
            "analyzed_table": "articles_analyzed",
            "data_dir": tmp_path,
            "outputs_dir": tmp_path / "out",
        },
        news=NewsConfig(
            start_date="2023-01-01",
            end_date="2023-01-02",
            keywords=["bullying"],
            domains=["example.com"],
        ),
    )
    upsert_json_rows(
        db_path,
        config.storage.clean_table,
        [
            {
                "url": "https://example.com/1",
                "source_domain": "example.com",
                "title": "Sample",
                "body_text": "Students face bullying in school environments which affects mental health.",
                "published_at": "2023-01-01T00:00:00",
                "language": "en",
                "was_translated": 0,
                "content_hash": "hash1",
            },
            {
                "url": "https://example.com/2",
                "source_domain": "example.com",
                "title": "Sample 2",
                "body_text": "Universities tackle cyber issues and provide mental support to students.",
                "published_at": "2023-01-02T00:00:00",
                "language": "en",
                "was_translated": 0,
                "content_hash": "hash2",
            },
        ],
    )
    return config


def test_analyze_articles_returns_expected_frames(analyzed_config: AppConfig) -> None:
    results = analyze_articles(analyzed_config)
    assert set(results.keys()) == {"tfidf", "cooccurrence", "sentiment", "articles"}
    articles_df = results["articles"]
    assert not articles_df.empty
    assert "keywords" in articles_df.columns
    assert "article_sentiment" in articles_df.columns


def test_sentiment_merge_preserves_non_midnight_timestamp(analyzed_config: AppConfig) -> None:
    db_path = analyzed_config.storage.database_path
    upsert_json_rows(
        db_path,
        analyzed_config.storage.clean_table,
        [
            {
                "url": "https://example.com/late",
                "source_domain": "example.com",
                "title": "Late Publication",
                "body_text": "This article is wonderful, amazing, and fantastic.",
                "published_at": "2023-01-04T15:30:00",
                "language": "en",
                "was_translated": 0,
                "content_hash": "hash3",
            }
        ],
    )

    results = analyze_articles(analyzed_config)
    articles_df = results["articles"]
    late_article = articles_df.loc[articles_df["url"] == "https://example.com/late"].iloc[0]
    expected_sentiment = TextBlob(late_article["body_text"]).sentiment.polarity
    assert late_article["article_sentiment"] == pytest.approx(expected_sentiment)
    assert pd.to_datetime(late_article["published_at_window"]).hour == 0

    sentiment_df = results["sentiment"]
    window_match = sentiment_df.loc[
        pd.to_datetime(sentiment_df["published_at"]) == pd.to_datetime(late_article["published_at_window"])
    ]
    assert not window_match.empty
    assert window_match.iloc[0]["sentiment"] == pytest.approx(expected_sentiment)
