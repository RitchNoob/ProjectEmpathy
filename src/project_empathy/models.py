"""Pydantic models for Project Empathy."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ArticleRaw(BaseModel):
    """Representation of a raw article."""

    url: str
    source_domain: str
    title: Optional[str]
    body_text: Optional[str]
    published_at: Optional[datetime]
    language: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    content_hash: Optional[str]


class ArticleClean(BaseModel):
    """Cleaned article representation."""

    url: str
    source_domain: str
    title: str
    body_text: str
    published_at: Optional[datetime]
    language: str
    was_translated: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    content_hash: str


class ArticleAnalyzed(BaseModel):
    """Analyzed article representation."""

    url: str
    source_domain: str
    title: str
    body_text: str
    published_at: Optional[datetime]
    language: str
    was_translated: bool
    sentiment: float
    keywords: list[str]
    categories: list[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
