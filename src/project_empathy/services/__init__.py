"""Service layer exports."""

from .orders import create_order, mark_order_status
from .statistics import compute_dashboard_stats
from .subscriptions import ensure_active_subscription, record_usage, sync_subscription_plan
# Telephony helpers rely on the external Twilio dependency which isn't available in
# the execution sandbox. Import them lazily so that the rest of the service layer
# remains functional during tests.
try:  # pragma: no cover - best effort import
    from .telephony import TwilioCallContext, build_greeting_response, handle_transcription
except ModuleNotFoundError:  # pragma: no cover - exercised when twilio package missing
    TwilioCallContext = None  # type: ignore[assignment]

    def build_greeting_response(*_args, **_kwargs):  # type: ignore[override]
        raise RuntimeError("Twilio dependency is not installed")

    def handle_transcription(*_args, **_kwargs):  # type: ignore[override]
        raise RuntimeError("Twilio dependency is not installed")

__all__ = [
    "create_order",
    "mark_order_status",
    "compute_dashboard_stats",
    "ensure_active_subscription",
    "record_usage",
    "sync_subscription_plan",
    "TwilioCallContext",
    "build_greeting_response",
    "handle_transcription",
]
