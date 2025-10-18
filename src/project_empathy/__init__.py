"""Project Empathy package."""

from importlib.metadata import version

__all__ = ["get_version"]


def get_version() -> str:
    """Return package version."""
    try:
        return version("project_empathy")
    except Exception:  # pragma: no cover - fallback when metadata missing
        return "0.0.0"
