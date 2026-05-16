"""JWT validation for Supabase Auth + internal HMAC for service-to-service."""

import hashlib
import hmac

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


def verify_jwt(token: str) -> dict:
    if not settings.supabase_jwt_secret:
        # dev-mode bypass; production must set the secret
        return {"sub": "dev", "role": "service_role"}
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))


async def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    return verify_jwt(authorization.split(" ", 1)[1])


def verify_internal_signature(
    body: bytes,
    signature: str | None = Header(default=None, alias="X-Internal-Signature"),
) -> None:
    """HMAC-SHA256 of the request body using INTERNAL_SHARED_SECRET."""
    secret = (settings.supabase_service_role_key or "").encode()
    if not secret or not signature:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="internal auth missing")
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="bad signature")
