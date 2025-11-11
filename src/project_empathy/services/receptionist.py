"""Utilities for transforming receptionist profiles for presentation."""

from __future__ import annotations

from typing import Iterable, Optional

from ..ai.assistant import build_system_prompt


def _sanitize_language(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.strip()
    return normalized or None


def _unique_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value:
            continue
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def build_profile_preview(profile: object) -> dict[str, object]:
    """Return a serialisable snapshot describing how the concierge behaves."""

    languages = _unique_preserving_order(
        [
            _sanitize_language(getattr(profile, "primary_language", None)),
            _sanitize_language(getattr(profile, "secondary_language", None)),
        ]
    )

    upsell_phrases = getattr(profile, "upsell_phrases", None) or []
    if isinstance(upsell_phrases, list):
        upsell_phrases = [phrase.strip() for phrase in upsell_phrases if phrase and phrase.strip()]
    else:
        upsell_phrases = []

    preview = {
        "system_prompt": build_system_prompt(profile),
        "greeting": getattr(profile, "greeting", ""),
        "closing_remark": getattr(profile, "closing_remark", ""),
        "upsell_phrases": upsell_phrases,
        "tone": getattr(profile, "tone", ""),
        "voice_name": getattr(profile, "voice_name", ""),
        "languages": languages,
        "signature": getattr(profile, "signature", None),
        "persona": getattr(profile, "display_name", None),
    }

    custom_instructions = getattr(profile, "custom_instructions", None)
    if custom_instructions:
        preview["custom_instructions"] = custom_instructions

    return preview


__all__ = ["build_profile_preview"]
