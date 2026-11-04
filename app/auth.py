import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import User, UserSession

password_hash = PasswordHasher()
bearer = HTTPBearer(auto_error=False)


def digest_token(token: str) -> str:
    return hmac.new(settings.session_token_pepper.encode(), token.encode(), hashlib.sha256).hexdigest()


def issue_session(db: Session, user: User) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.session_ttl_days)
    db.add(UserSession(user_id=user.id, token_digest=digest_token(token), expires_at=expires_at))
    db.commit()
    return token, expires_at


def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> UserSession:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    session = db.scalar(select(UserSession).where(UserSession.token_digest == digest_token(credentials.credentials)))
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at if session is not None else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if session is None or session.revoked_at is not None or expires_at <= now or not session.user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return session


def get_current_user(session: UserSession = Depends(get_current_session)) -> User:
    return session.user
