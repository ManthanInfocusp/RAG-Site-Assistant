"""Password hashing, signed session cookies, and API key helpers."""

from __future__ import annotations

import secrets

import bcrypt
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.core.config import settings

_serializer = URLSafeTimedSerializer(settings.secret_key, salt="session")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


def create_session_token(user_id: str) -> str:
    """Sign the user_id into an opaque, time-limited token for the session cookie."""
    return _serializer.dumps({"sub": user_id})


def read_session_token(token: str) -> str | None:
    """Return the user_id from the session token, or None if invalid/expired."""
    try:
        data = _serializer.loads(token, max_age=settings.session_ttl_seconds)
        return data.get("sub")
    except BadSignature:
        return None
    except Exception:
        return None


def generate_public_key() -> str:
    """Used in the embed script (data-site-key)."""
    return "pk_live_" + secrets.token_urlsafe(24)


def generate_secret_key() -> str:
    """Server-to-server key for portal API calls (currently unused but reserved)."""
    return "sk_live_" + secrets.token_urlsafe(32)
