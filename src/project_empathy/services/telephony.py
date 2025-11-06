"""Telephony helper utilities for Twilio integration."""

from __future__ import annotations

from typing import Dict

from twilio.twiml.voice_response import VoiceResponse

from ..ai.assistant import send_message


class TwilioCallContext:
    """A simple call context carrying conversation history."""

    def __init__(self) -> None:
        self.history: list[dict] = []

    def add_exchange(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})


def build_greeting_response() -> str:
    """Return a TwiML greeting to start the call."""

    response = VoiceResponse()
    response.say("Bonjour, ici le restaurant. Comment puis-je vous aider aujourd'hui ?", voice="alice", language="fr-FR")
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

    context.add_exchange("user", transcription)
    message = send_message(context.history, transcription)
    context.add_exchange("assistant", message)
    response = VoiceResponse()
    response.say(message, voice="alice", language="fr-FR")
    response.record(action="/api/v1/twilio/handle-input", max_length=30, transcribe=True, play_beep=True)
    return {"twiml": str(response), "message": message}


__all__ = ["build_greeting_response", "handle_transcription", "TwilioCallContext"]
