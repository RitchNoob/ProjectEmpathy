"""Configuration handling for Project Empathy."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, validator

from .logging_utils import get_logger

LOGGER = get_logger("config")


class StorageConfig(BaseModel):
    """Storage related configuration."""

    database_path: Path = Field(default=Path("data/empathy.db"))
    raw_table: str = Field(default="articles_raw")
    clean_table: str = Field(default="articles_clean")
    analyzed_table: str = Field(default="articles_analyzed")
    data_dir: Path = Field(default=Path("data"))
    outputs_dir: Path = Field(default=Path("outputs"))


class NewsConfig(BaseModel):
    """News related configuration."""

    start_date: str
    end_date: str
    languages: List[str] = Field(default_factory=lambda: ["en", "ms", "zh"])
    keywords: List[str]
    domains: List[str]
    request_interval_seconds: float = 3.0
    robots_cache_hours: int = 12

    @validator("languages", each_item=True)
    def lower_lang(cls, value: str) -> str:  # noqa: D401
        """Lowercase language codes."""

        return value.lower()


class PipelineConfig(BaseModel):
    """Pipeline stage configuration."""

    translate_non_english: bool = True
    tfidf_top_k: int = 20
    cooccurrence_window: int = 2
    sentiment_time_window: str = "D"
    min_article_length: int = 300
    chunk_size: int = 50


class ReportConfig(BaseModel):
    """Report metadata configuration."""

    title: str = "Project Empathy Report"
    description: Optional[str] = None


class AppConfig(BaseModel):
    """Root application configuration."""

    storage: StorageConfig = Field(default_factory=StorageConfig)
    news: NewsConfig
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)


def load_config(path: Path) -> AppConfig:
    """Load application configuration from YAML file."""

    LOGGER.info("Loading configuration from %s", path)
    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)
    config = AppConfig(**raw)
    LOGGER.debug("Loaded configuration: %s", config.json())
    return config


def write_default_config(path: Path) -> None:
    """Write default configuration example to the provided path."""

    LOGGER.info("Writing default configuration to %s", path)
    example_path = Path(__file__).resolve().parents[2] / "config.example.yaml"
    if not example_path.exists():
        raise FileNotFoundError("config.example.yaml not found")
    content = example_path.read_text(encoding="utf-8")
    path.write_text(content, encoding="utf-8")
