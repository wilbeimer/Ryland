import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.db import (
    confirm_verification,
    delete_session_hash,
    get_user_by_session_hash,
    insert_session,
    replace_verification_token,
)
from backend.models import User
from backend.passwords import hash_token

bearer_scheme = HTTPBearer(auto_error=False)
_VERIFICATION_TTL = timedelta(hours=24)
_SESSION_TTL = timedelta(days=14)


def verification_link(token: str) -> str:
    base = os.getenv("APP_PUBLIC_URL", "http://localhost:5173").strip().rstrip("/")
    if not base:
        base = "http://localhost:5173"
    return f"{base}/verify-email?{urlencode({'token': token})}"


def issue_verification_token(user_id: UUID) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(UTC) + _VERIFICATION_TTL).isoformat()
    replace_verification_token(user_id, hash_token(token), expires_at)
    return token


def confirm_email_token(token: str) -> bool:
    return confirm_verification(hash_token(token), datetime.now(UTC).isoformat())


def start_session(user_id: UUID) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(UTC) + _SESSION_TTL).isoformat()
    insert_session(user_id, hash_token(token), expires_at)
    return token


def end_session(token: str) -> None:
    delete_session_hash(hash_token(token))


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Sign in required")
    user = get_user_by_session_hash(hash_token(credentials.credentials))
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in required")
    if not user.email_verified:
        raise HTTPException(
            status_code=403, detail="Confirm your email before continuing"
        )
    return user
