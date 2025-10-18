from pathlib import Path

import pytest

pytest.importorskip("pandas")

from project_empathy.clean import clean_articles
from project_empathy.config import AppConfig, NewsConfig
from project_empathy.db import init_db, upsert_json_rows


@pytest.fixture()
def temp_config(tmp_path: Path) -> AppConfig:
    db_path = tmp_path / "empathy.db"
    init_db(db_path)
    return AppConfig(
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


def test_clean_articles_filters_short_entries(temp_config: AppConfig) -> None:
    db_path = temp_config.storage.database_path
    upsert_json_rows(
        db_path,
        temp_config.storage.raw_table,
        [
            {
                "url": "https://example.com/1",
                "source_domain": "example.com",
                "title": "Sample",
                "body_text": "This is a long body " * 50,
                "published_at": "2023-01-01T00:00:00",
                "language": "en",
                "content_hash": "hash1",
            },
            {
                "url": "https://example.com/2",
                "source_domain": "example.com",
                "title": "Short",
                "body_text": "short",
                "published_at": "2023-01-01T00:00:00",
                "language": "en",
                "content_hash": "hash2",
            },
        ],
    )
    df = clean_articles(temp_config)
    assert len(df) == 1
    assert df.iloc[0]["url"] == "https://example.com/1"
