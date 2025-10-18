"""Export routines for Project Empathy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from .config import AppConfig
from .db import read_table
from .logging_utils import get_logger
from .utils import ensure_directory

LOGGER = get_logger("export")


def export_outputs(config: AppConfig) -> Dict[str, Path]:
    """Export analysis results to CSV and HTML report."""

    storage = config.storage
    outputs_dir = Path(storage.outputs_dir)
    ensure_directory(outputs_dir)
    db_path = storage.database_path
    articles = read_table(db_path, storage.analyzed_table)
    if articles.empty:
        LOGGER.warning("No analyzed articles to export")
        return {}
    articles = _normalize_columns(articles)
    articles_master = outputs_dir / "articles_master.csv"
    metrics_daily = outputs_dir / "metrics_daily.csv"
    keyword_freq = outputs_dir / "keyword_freq.csv"
    report_html = outputs_dir / "report.html"

    articles.to_csv(articles_master, index=False)
    sentiment_daily = (
        articles[["published_at", "article_sentiment"]]
        .dropna()
        .assign(published_at=lambda df: pd.to_datetime(df["published_at"]))
        .groupby(pd.Grouper(key="published_at", freq=config.pipeline.sentiment_time_window))
        .mean(numeric_only=True)
        .reset_index()
    )
    sentiment_daily.to_csv(metrics_daily, index=False)

    keyword_rows = []
    for _, row in articles.iterrows():
        for keyword in row.get("keywords", []):
            keyword_rows.append({"url": row["url"], "keyword": keyword})
    pd.DataFrame(keyword_rows, columns=["url", "keyword"]).to_csv(keyword_freq, index=False)

    _write_report(report_html, articles, sentiment_daily)

    LOGGER.info("Exported outputs to %s", outputs_dir)
    return {
        "articles_master": articles_master,
        "metrics_daily": metrics_daily,
        "keyword_freq": keyword_freq,
        "report": report_html,
    }


def _normalize_columns(articles: pd.DataFrame) -> pd.DataFrame:
    articles = articles.copy()
    if "keywords" in articles.columns:
        articles["keywords"] = articles["keywords"].apply(_ensure_list)
    if "categories" in articles.columns:
        articles["categories"] = articles["categories"].apply(_ensure_list)
    if "was_translated" in articles.columns:
        articles["was_translated"] = articles["was_translated"].astype(bool)
    return articles


def _ensure_list(value) -> List[str]:  # type: ignore[override]
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            return [value]
    return []


def _write_report(path: Path, articles: pd.DataFrame, sentiment_daily: pd.DataFrame) -> None:
    total_articles = len(articles)
    avg_sentiment = articles["article_sentiment"].mean()
    sentiment_chart = sentiment_daily.to_html(index=False)
    html = f"""
    <html>
    <head>
        <title>Project Empathy Report</title>
        <meta charset="utf-8" />
        <style>
            body {{ font-family: Arial, sans-serif; margin: 2rem; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Project Empathy Report</h1>
        <p>Total articles analyzed: {total_articles}</p>
        <p>Average sentiment: {avg_sentiment:.2f}</p>
        <h2>Sentiment Over Time</h2>
        {sentiment_chart}
    </body>
    </html>
    """
    path.write_text(html, encoding="utf-8")
