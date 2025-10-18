"""Scraping utilities for Project Empathy."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from langdetect import detect
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from .config import AppConfig
from .db import init_db, upsert_json_rows
from .logging_utils import get_logger
from .models import ArticleRaw
from .utils import RateLimiter, hash_text, load_environment

LOGGER = get_logger("scrape")

DEFAULT_HEADERS = {
    "User-Agent": "ProjectEmpathyBot/0.1 (+https://example.com/project-empathy)",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_url(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Optional[str]:
    """Fetch URL content with retries."""

    LOGGER.debug("Fetching URL: %s", url)
    headers = {**DEFAULT_HEADERS, **(headers or {})}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _get() -> str:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text

    try:
        return _get()
    except RetryError as exc:
        LOGGER.error("Failed to fetch %s: %s", url, exc)
        return None


def parse_article(html: str, domain: str) -> Optional[ArticleRaw]:
    """Parse HTML content into an ArticleRaw model."""

    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("title")
    body_candidates = soup.find_all("p")
    body_text = "\n".join(p.get_text(strip=True) for p in body_candidates)
    if not body_text:
        LOGGER.warning("No body text extracted for domain %s", domain)
        return None
    published_at = _extract_date(soup)
    language = _detect_language(body_text)
    normalized = " ".join(body_text.split())
    content_hash = hash_text(normalized)
    return ArticleRaw(
        url="",
        source_domain=domain,
        title=title.get_text(strip=True) if title else None,
        body_text=normalized,
        published_at=published_at,
        language=language,
        content_hash=content_hash,
    )


def _extract_date(soup: BeautifulSoup) -> Optional[datetime]:
    for selector in ["meta[property='article:published_time']", "meta[name='pubdate']", "time"]:
        tag = soup.select_one(selector)
        if tag:
            content = tag.get("content") or tag.get("datetime") or tag.get_text(strip=True)
            if content:
                try:
                    return datetime.fromisoformat(content.replace("Z", "+00:00"))
                except ValueError:
                    continue
    return None


def _detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "en"


def crawl(config: AppConfig) -> None:  # pragma: no cover - network heavy
    """Crawl configured domains and persist to database."""

    env = load_environment()
    headers = {"User-Agent": env.get("USER_AGENT", DEFAULT_HEADERS["User-Agent"]) }
    limiter = RateLimiter(interval=max(60.0 / float(env.get("REQUESTS_PER_MINUTE", 15)), 0.1))
    db_path = config.storage.database_path
    init_db(db_path)

    newsapi_key = env.get("NEWSAPI_KEY")
    articles: List[ArticleRaw] = []
    if newsapi_key:
        LOGGER.info("Fetching from NewsAPI")
        articles.extend(_fetch_newsapi(config, newsapi_key))

    for article in articles:
        _persist_article(article, db_path)

    LOGGER.info("Crawling individual domains for supplemental coverage")
    for domain in config.news.domains:
        limiter.wait()
        url = f"https://{domain}"
        html = fetch_url(url, headers=headers)
        if not html:
            continue
        article = parse_article(html, domain)
        if not article:
            continue
        article.url = url
        _persist_article(article, db_path)
        time.sleep(config.news.request_interval_seconds)


def _fetch_newsapi(config: AppConfig, api_key: str) -> List[ArticleRaw]:
    params = {
        "apiKey": api_key,
        "language": "en",
        "pageSize": 100,
        "from": config.news.start_date,
        "to": config.news.end_date,
        "q": " OR ".join(config.news.keywords),
        "domains": ",".join(config.news.domains),
    }
    url = "https://newsapi.org/v2/everything"
    LOGGER.debug("NewsAPI params: %s", json.dumps(params))
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()
    articles: List[ArticleRaw] = []
    for item in payload.get("articles", [])[:10]:
        domain = item.get("url", "").split("/")[2]
        article = ArticleRaw(
            url=item.get("url", ""),
            source_domain=domain,
            title=item.get("title"),
            body_text=item.get("content"),
            published_at=_parse_newsapi_date(item.get("publishedAt")),
            language=item.get("language"),
            content_hash=hash_text(item.get("content", "")) if item.get("content") else None,
        )
        articles.append(article)
    return articles


def _parse_newsapi_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _persist_article(article: ArticleRaw, db_path: Path) -> None:
    if not article.body_text:
        LOGGER.debug("Skipping article without body: %s", article.url)
        return
    if not article.url:
        LOGGER.debug("Skipping article without URL")
        return
    LOGGER.info("Persisting article: %s", article.url)
    row = article.dict()
    if isinstance(row.get("published_at"), datetime):
        row["published_at"] = row["published_at"].isoformat()
    upsert_json_rows(db_path, "articles_raw", [row])
