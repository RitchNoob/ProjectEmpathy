"""Conversational AI orchestration."""

from __future__ import annotations

from typing import Iterable, List

import openai

from ..config import get_settings

BASE_PROMPT = (
    "Tu es un réceptionniste de restaurant serviable et professionnel. "
    "Salue chaque client, réponds en français, propose des ventes additionnelles et "
    "confirme les commandes avant de terminer la conversation. Pose des questions "
    "pour clarifier si nécessaire."
)


def _build_messages(history: Iterable[dict], new_message: str) -> List[dict]:
    messages = [{"role": "system", "content": BASE_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": new_message})
    return messages


def send_message(history: Iterable[dict], new_message: str) -> str:
    """Send a message to the configured LLM provider."""

    settings = get_settings()
    if not settings.openai.api_key:
        raise RuntimeError("OpenAI API key is not configured")

    openai.api_key = settings.openai.api_key
    response = openai.ChatCompletion.create(  # type: ignore[attr-defined]
        model=settings.openai.model,
        messages=_build_messages(history, new_message),
        temperature=0.4,
        timeout=settings.openai.request_timeout,
    )
    return response["choices"][0]["message"]["content"].strip()


__all__ = ["send_message"]
