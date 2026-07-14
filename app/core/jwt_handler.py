from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create JWT access token.
    """

    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.access_token_expire_minutes)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token(
    data: dict[str, Any],
) -> str:

    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    to_encode = data.copy()

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_token(token: str):

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        return payload

    except JWTError:

        return None