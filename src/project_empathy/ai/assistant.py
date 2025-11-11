"""Conversational AI orchestration."""

from __future__ import annotations

from typing import Any, Iterable, List

try:  # pragma: no cover - import guarded for sandbox environments without OpenAI SDK
    import openai  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised in offline tests
    openai = None  # type: ignore[assignment]

from ..config import get_settings

BASE_PROMPT = (
    "Tu es un réceptionniste de restaurant serviable et professionnel. "
    "Salue chaque client, réponds en français, propose des ventes additionnelles et "
    "confirme les commandes avant de terminer la conversation. Pose des questions "
    "pour clarifier si nécessaire."
)


def _extract(profile: Any, attribute: str, default: Any = None) -> Any:
    if profile is None:
        return default
    if isinstance(profile, dict):
        return profile.get(attribute, default)
    return getattr(profile, attribute, default)


def build_system_prompt(profile: Any) -> str:
    if profile is None:
        return BASE_PROMPT

    parts: list[str] = [BASE_PROMPT]

    display_name = _extract(profile, "display_name")
    if display_name:
        parts.append(f"Présente-toi comme {display_name}.")

    tone = _extract(profile, "tone")
    if tone:
        parts.append(f"Adopte un ton {tone}.")

    personality = _extract(profile, "personality")
    if personality:
        parts.append(personality)

    primary_language = _extract(profile, "primary_language")
    secondary_language = _extract(profile, "secondary_language")
    if primary_language or secondary_language:
        languages = primary_language or "fr-FR"
        if secondary_language:
            languages = f"{languages} (prioritaire) et {secondary_language} (secondaire)"
        parts.append(
            "Réponds avec fluidité dans les langues suivantes : "
            f"{languages}. Favorise la langue demandée par le client."
        )

    upsell_phrases = _extract(profile, "upsell_phrases", []) or []
    if upsell_phrases:
        phrases = "; ".join(upsell_phrases)
        parts.append(
            "Propose élégamment des ventes additionnelles pertinentes, par exemple : "
            f"{phrases}."
        )

    custom_instructions = _extract(profile, "custom_instructions")
    if custom_instructions:
        parts.append(custom_instructions)

    closing_remark = _extract(profile, "closing_remark")
    if closing_remark:
        parts.append(f"Conclue en rappelant : {closing_remark}")

    signature = _extract(profile, "signature")
    if signature:
        parts.append(f"Signe poliment en mentionnant : {signature}.")

    return " ".join(parts)


def _build_messages(history: Iterable[dict], new_message: str, profile: Any) -> List[dict]:
    messages = [{"role": "system", "content": build_system_prompt(profile)}]
    messages.extend(history)
    messages.append({"role": "user", "content": new_message})
    return messages


def send_message(history: Iterable[dict], new_message: str, profile: Any | None = None) -> str:
    """Send a message to the configured LLM provider."""

    settings = get_settings()
    if not settings.openai.api_key:
        raise RuntimeError("OpenAI API key is not configured")

    if openai is None:
        raise RuntimeError("OpenAI SDK is not installed")

    openai.api_key = settings.openai.api_key
    response = openai.ChatCompletion.create(  # type: ignore[attr-defined]
        model=settings.openai.model,
        messages=_build_messages(history, new_message, profile),
        temperature=0.4,
        timeout=settings.openai.request_timeout,
    )
    return response["choices"][0]["message"]["content"].strip()


__all__ = ["send_message", "build_system_prompt"]
