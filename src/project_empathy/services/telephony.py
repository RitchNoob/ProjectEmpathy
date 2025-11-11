"""Telephony helper utilities for Twilio integration."""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    from twilio.twiml.voice_response import VoiceResponse  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - executed in sandbox
    VoiceResponse = None  # type: ignore[assignment]

    def _missing_dependency(*_args, **_kwargs):
        raise RuntimeError("Twilio dependency is not installed") from exc

from ..ai.assistant import send_message


class TwilioCallContext:
    """A simple call context carrying conversation history and persona."""

    def __init__(self, profile: Any | None = None) -> None:
        self.history: list[dict] = []
        self.profile = profile

    def add_exchange(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})


def _profile_attr(profile: Any | None, attribute: str, default: Any) -> Any:
    if profile is None:
        return default
    if isinstance(profile, dict):
        return profile.get(attribute, default)
    return getattr(profile, attribute, default)


def build_greeting_response(profile: Any | None = None) -> str:
    """Return a TwiML greeting to start the call."""

    if VoiceResponse is None:  # pragma: no cover - executed when dependency missing
        _missing_dependency()

    greeting = _profile_attr(
        profile,
        "greeting",
        "Bonjour, ici le restaurant. Comment puis-je vous aider aujourd'hui ?",
    )
    voice = _profile_attr(profile, "voice_name", "alice")
    language = _profile_attr(profile, "primary_language", "fr-FR")

    response = VoiceResponse()
    response.say(greeting, voice=voice, language=language)
    response.pause(length=1)
    response.record(
        action="/api/v1/twilio/handle-input",
        max_length=30,
        transcribe=True,
        play_beep=True,
    )
    return str(response)


def handle_transcription(context: TwilioCallContext, transcription: str) -> Dict[str, str]:
    """Generate a spoken response for the caller using the AI assistant."""

    if VoiceResponse is None:  # pragma: no cover - executed when dependency missing
        _missing_dependency()

    context.add_exchange("user", transcription)
    message = send_message(context.history, transcription, context.profile)
    context.add_exchange("assistant", message)
    response = VoiceResponse()
    voice = _profile_attr(context.profile, "voice_name", "alice")
    language = _profile_attr(context.profile, "primary_language", "fr-FR")
    response.say(message, voice=voice, language=language)
    response.record(action="/api/v1/twilio/handle-input", max_length=30, transcribe=True, play_beep=True)
    return {"twiml": str(response), "message": message}


__all__ = ["build_greeting_response", "handle_transcription", "TwilioCallContext"]
