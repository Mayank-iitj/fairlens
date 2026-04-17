from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_token, get_password_hash
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import GoogleAuthRequest, RefreshRequest, TokenResponse


router = APIRouter()


@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    configured_client_ids = [cid.strip() for cid in settings.google_client_ids if cid and cid.strip()]
    if settings.google_client_id.strip():
        configured_client_ids.append(settings.google_client_id.strip())

    # Keep order deterministic while deduplicating.
    configured_client_ids = list(dict.fromkeys(configured_client_ids))

    if not configured_client_ids:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google auth is not configured. Set GOOGLE_CLIENT_ID or GOOGLE_CLIENT_IDS.",
        )

    try:
        token_info = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token") from exc

    audience = token_info.get("aud")
    if audience not in configured_client_ids:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience")

    issuer = token_info.get("iss", "")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")

    email = token_info.get("email")
    email_verified = token_info.get("email_verified", False)
    if not email or not email_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google account email not verified")

    user = db.scalar(select(User).where(User.email == email))
    if not user:
        name = token_info.get("name") or email.split("@", maxsplit=1)[0]
        # Keep a non-empty hash since the table currently requires it.
        placeholder_password = f"google-oauth-{uuid4()}"
        user = User(
            email=email,
            name=name,
            hashed_password=get_password_hash(placeholder_password),
            role="Admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return TokenResponse(
        access_token=create_token(user.id, settings.access_token_expire_minutes),
        refresh_token=create_token(user.id, settings.refresh_token_expire_minutes, {"type": "refresh"}),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        claims = jwt.decode(payload.refresh_token, settings.secret_key, algorithms=[settings.algorithm])
        if claims.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = claims.get("sub")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return TokenResponse(
        access_token=create_token(user.id, settings.access_token_expire_minutes),
        refresh_token=create_token(user.id, settings.refresh_token_expire_minutes, {"type": "refresh"}),
    )
