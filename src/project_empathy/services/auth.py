"""API key issuance and verification helpers."""

from __future__ import annotations

from datetime import datetime
import hashlib
import secrets
from typing import Tuple

from sqlalchemy.orm import Session

from ..models import ApiToken, Restaurant


TOKEN_PREFIX_LENGTH = 8


class InvalidApiKey(RuntimeError):
    """Raised when an API key cannot be validated."""


def _hash_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _generate_token_value() -> Tuple[str, str, str]:
    raw = secrets.token_urlsafe(32)
    prefix = raw[:TOKEN_PREFIX_LENGTH]
    hashed = _hash_key(raw)
    return prefix, hashed, raw


def issue_api_token(session: Session, restaurant: Restaurant, name: str) -> Tuple[ApiToken, str]:
    """Create a new API token for a restaurant and return the plaintext value."""

    prefix, hashed, raw = _generate_token_value()
    token = ApiToken(
        restaurant=restaurant,
        name=name,
        prefix=prefix,
        hashed_key=hashed,
    )
    session.add(token)
    session.flush()
    return token, raw


def verify_api_key(session: Session, value: str) -> ApiToken:
    """Validate an API key string and return the matching token."""

    token = _lookup_token(session, value)
    if token is None or token.revoked:
        raise InvalidApiKey("Invalid API key provided")

    expected = _hash_key(value)
    if not secrets.compare_digest(expected, token.hashed_key):
        raise InvalidApiKey("Invalid API key provided")

    token.last_used_at = datetime.utcnow()
    session.add(token)
    session.flush()
    return token


def rotate_api_token(session: Session, token: ApiToken) -> str:
    """Rotate the secret for an existing token and return the new plaintext value."""

    prefix, hashed, raw = _generate_token_value()
    token.prefix = prefix
    token.hashed_key = hashed
    token.revoked = False
    token.last_used_at = None
    session.add(token)
    session.flush()
    return raw


def revoke_api_token(session: Session, token: ApiToken) -> None:
    """Soft-delete an API token."""

    token.revoked = True
    session.add(token)
    session.flush()


def _lookup_token(session: Session, value: str) -> ApiToken | None:
    if not value:
        return None
    prefix = value[:TOKEN_PREFIX_LENGTH]
    return (
        session.query(ApiToken)
            .filter(ApiToken.prefix == prefix)
            .one_or_none()
    )


__all__ = [
    "issue_api_token",
    "verify_api_key",
    "rotate_api_token",
    "revoke_api_token",
    "InvalidApiKey",
]
