from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db import models
from app.db.session import engine, get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/google", auto_error=False)


def _get_or_create_guest_user(db: Session) -> models.User:
    Base.metadata.create_all(bind=engine)

    guest_email = "guest@fairlens.local"
    guest = db.query(models.User).filter(models.User.email == guest_email).first()
    if guest:
        return guest

    guest = models.User(
        email=guest_email,
        name="Guest Workspace",
        hashed_password="guest-mode",
        role="Admin",
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    if not token:
        return _get_or_create_guest_user(db)

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        if not user_id:
            return _get_or_create_guest_user(db)
    except JWTError as exc:
        return _get_or_create_guest_user(db)
    user = db.get(models.User, user_id)
    if not user:
        return _get_or_create_guest_user(db)
    return user
