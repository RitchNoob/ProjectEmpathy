"""Twilio webhook endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, status

try:  # pragma: no cover - exercised only when Twilio is installed
    from ..services.telephony import TwilioCallContext, build_greeting_response, handle_transcription
    from ..db import SessionLocal
    from ..models import Restaurant
except (RuntimeError, ModuleNotFoundError):  # pragma: no cover - Twilio missing in sandbox
    TwilioCallContext = None  # type: ignore[assignment]

    def build_greeting_response() -> str:  # type: ignore[override]
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Twilio integration unavailable")

    def handle_transcription(*_args, **_kwargs):  # type: ignore[override]
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Twilio integration unavailable")

    SessionLocal = None  # type: ignore[assignment]
else:

    def _create_call_context() -> TwilioCallContext:
        if SessionLocal is None:  # pragma: no cover - defensive
            return TwilioCallContext()

        session = SessionLocal()
        try:
            restaurant = session.query(Restaurant).order_by(Restaurant.id.asc()).first()
            profile = getattr(restaurant, "receptionist_profile", None) if restaurant else None
            if profile is not None:
                session.expunge(profile)
            return TwilioCallContext(profile=profile)
        finally:
            session.close()


router = APIRouter(prefix="/twilio", tags=["twilio"])


@router.post("/voice", response_class=None)
def inbound_call() -> str:
    """Respond to Twilio voice webhook with greeting."""

    if TwilioCallContext is None:  # pragma: no cover - Twilio missing in sandbox
        return build_greeting_response()

    global _call_context
    _call_context = _create_call_context()
    return build_greeting_response(_call_context.profile)


_call_context = None  # type: ignore[assignment]


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
