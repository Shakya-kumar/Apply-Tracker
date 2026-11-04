from datetime import datetime, timezone

from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_session, get_current_user, issue_session, password_hash
from app.db import get_db
from app.models import Membership, Tenant, User
from app.schemas import LoginRequest, RegisterRequest, SessionResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user = User(email=email, password_hash=password_hash.hash(payload.password))
    db.add(user)
    try:
        db.flush()
        tenant = Tenant(name=f"{email.split('@', 1)[0]}'s workspace")
        db.add(tenant)
        db.flush()
        db.add(Membership(user_id=user.id, tenant_id=tenant.id, role="owner"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from None
    token, expires_at = issue_session(db, user)
    return SessionResponse(access_token=token, expires_at=expires_at)


@router.post("/login", response_model=SessionResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    try:
        valid_password = user is not None and password_hash.verify(user.password_hash, payload.password)
    except VerifyMismatchError:
        valid_password = False
    if not valid_password or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token, expires_at = issue_session(db, user)
    return SessionResponse(access_token=token, expires_at=expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(session=Depends(get_current_session), db: Session = Depends(get_db)):
    session.revoked_at = datetime.now(timezone.utc)
    db.commit()


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
