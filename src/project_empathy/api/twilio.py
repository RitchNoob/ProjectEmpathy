"""Twilio webhook endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Form

from ..services.telephony import TwilioCallContext, build_greeting_response, handle_transcription

router = APIRouter(prefix="/twilio", tags=["twilio"])


@router.post("/voice", response_class=None)
def inbound_call() -> str:
    """Respond to Twilio voice webhook with greeting."""

    return build_greeting_response()


_call_context = TwilioCallContext()


@router.post("/handle-input")
def handle_input(
    TranscriptionText: str = Form(..., description="Transcribed text from Twilio"),
) -> str:
    """Handle transcription callbacks from Twilio."""

    result = handle_transcription(_call_context, TranscriptionText)
    return result["twiml"]


__all__ = ["router"]
