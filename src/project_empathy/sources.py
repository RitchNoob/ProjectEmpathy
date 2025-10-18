"""Source definitions for Project Empathy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class Source:
    """Representation of a news source."""

    name: str
    domain: str
    language: str


SOURCES: List[Source] = [
    Source("The Star", "thestar.com.my", "en"),
    Source("Free Malaysia Today", "freemalaysiatoday.com", "en"),
    Source("Malay Mail", "malaymail.com", "en"),
    Source("Channel NewsAsia Asia", "channelnewsasia.com", "en"),
    Source("Berita Harian", "bharian.com.my", "ms"),
    Source("Harian Metro", "hmetro.com.my", "ms"),
    Source("Utusan", "utusan.com.my", "ms"),
    Source("Sin Chew Daily", "sinchew.com.my", "zh"),
    Source("China Press", "chinapress.com.my", "zh"),
]


def sources_by_domain() -> Dict[str, Source]:
    """Return mapping of domain to source."""

    return {source.domain: source for source in SOURCES}


def source_domains() -> Iterable[str]:
    """Return iterable of all source domains."""

    return [source.domain for source in SOURCES]
