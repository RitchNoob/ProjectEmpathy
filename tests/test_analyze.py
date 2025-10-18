from pathlib import Path

import pytest

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
