"""Twilio webhook endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, status

try:  # pragma: no cover - exercised only when Twilio is installed
    from ..services.telephony import TwilioCallContext, build_greeting_response, handle_transcription
except (RuntimeError, ModuleNotFoundError):  # pragma: no cover - Twilio missing in sandbox
    TwilioCallContext = None  # type: ignore[assignment]

    def build_greeting_response() -> str:  # type: ignore[override]
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Twilio integration unavailable")

    def handle_transcription(*_args, **_kwargs):  # type: ignore[override]
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Twilio integration unavailable")

router = APIRouter(prefix="/twilio", tags=["twilio"])


@router.post("/voice", response_class=None)
def inbound_call() -> str:
    """Respond to Twilio voice webhook with greeting."""

    return build_greeting_response()


_call_context = TwilioCallContext() if TwilioCallContext else None


@router.post("/handle-input")
def handle_input(
    TranscriptionText: str = Form(..., description="Transcribed text from Twilio"),
) -> str:
    """Handle transcription callbacks from Twilio."""

    if not _call_context:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Twilio integration unavailable")

    result = handle_transcription(_call_context, TranscriptionText)
    return result["twiml"]


__all__ = ["router"]
