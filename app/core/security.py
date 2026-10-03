import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

_hasher = PasswordHasher()
# Hash dummy untuk menyamakan waktu respon saat email tidak ditemukan (anti user-enumeration).
_DUMMY_HASH = _hasher.hash("contentsy-dummy-password")

ACCESS_TOKEN_TYPE = "access"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerificationError, InvalidHashError):
        return False


def verify_dummy_password(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


def password_needs_rehash(hashed: str) -> bool:
    return _hasher.check_needs_rehash(hashed)


def create_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    """Return (token, expires_in_seconds)."""
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + expires_delta,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> uuid.UUID | None:
    """Return user id kalau token valid, None kalau invalid/expired/salah tipe."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "type"]},
        )
        if payload.get("type") != ACCESS_TOKEN_TYPE:
            return None
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, TypeError):
        return None
