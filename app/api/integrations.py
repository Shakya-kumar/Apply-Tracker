import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.config import settings
from app.db import get_db
from app.models import Application, ApplicationEvent, CalendarEvent, ConnectedAccount, EmailEvent, GoogleOAuthState, User
from app.schemas import APPLICATION_STATUSES

router = APIRouter(prefix="/integrations", tags=["integrations"])
GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
CALENDAR_API = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
SERVICE_SCOPES = {
    "gmail": ["https://www.googleapis.com/auth/gmail.metadata"],
    "calendar": ["https://www.googleapis.com/auth/calendar.events.readonly"],
}
BASE_SCOPES = ["openid", "email"]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def oauth_ready() -> bool:
    if not settings.google_client_id or not settings.google_client_secret or not settings.token_encryption_key:
        return False
    try:
        Fernet(settings.token_encryption_key.encode())
    except (ValueError, TypeError):
        return False
    return True


def cipher() -> Fernet:
    try:
        return Fernet(settings.token_encryption_key.encode())
    except (ValueError, TypeError):
        raise HTTPException(status_code=503, detail="OAuth token encryption is not configured") from None


def encrypt(value: str) -> str:
    return cipher().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    try:
        return cipher().decrypt(value.encode()).decode()
    except InvalidToken:
        raise HTTPException(status_code=503, detail="Stored integration token could not be decrypted; check TOKEN_ENCRYPTION_KEY") from None


def frontend_redirect(result: str) -> RedirectResponse:
    base = settings.frontend_url.rstrip("/")
    return RedirectResponse(f"{base}/integrations?google={result}", status_code=303)


def get_connection(db: Session, user_id: int, provider: str) -> ConnectedAccount | None:
    return db.scalar(select(ConnectedAccount).where(ConnectedAccount.user_id == user_id, ConnectedAccount.provider == provider))


@router.get("/status")
def integration_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = []
    for service, title in [("gmail", "Gmail"), ("calendar", "Google Calendar")]:
        account = get_connection(db, user.id, service)
        if account and account.status == "connected":
            items.append({"id": service, "name": title, "status": "connected", "connected": True, "account": account.provider_email, "last_synced_at": account.last_synced_at, "message": "Connected using a read-only Google permission."})
        elif not oauth_ready():
            items.append({"id": service, "name": title, "status": "setup_required", "connected": False, "account": None, "last_synced_at": None, "message": "Google OAuth credentials and token encryption key are not configured on the API."})
        else:
            items.append({"id": service, "name": title, "status": "available", "connected": False, "account": None, "last_synced_at": None, "message": "Available to connect using Google OAuth."})
    items.extend([
        {"id": "job_portals", "name": "Job portals", "status": "assisted_only", "connected": False, "account": None, "last_synced_at": None, "message": "Portal OAuth and account history imports are not implemented. Use official sites and add opportunities manually."},
        {"id": "chrome_extension", "name": "Chrome extension", "status": "not_available", "connected": False, "account": None, "last_synced_at": None, "message": "The extension has not been built yet."},
    ])
    return {"items": items}


@router.post("/google/start")
def start_google_oauth(service: str = Query(pattern="^(gmail|calendar)$"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not oauth_ready():
        raise HTTPException(status_code=503, detail="Google OAuth is not configured on this API")
    state = secrets.token_urlsafe(48)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    db.add(GoogleOAuthState(user_id=user.id, service=service, state_digest=hashlib.sha256(state.encode()).hexdigest(), code_verifier=verifier, expires_at=now_utc() + timedelta(minutes=10)))
    db.commit()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(BASE_SCOPES + SERVICE_SCOPES[service]),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "include_granted_scopes": "true",
    }
    return {"authorization_url": f"{GOOGLE_AUTH}?{urlencode(params)}"}


@router.get("/google/callback", include_in_schema=False)
async def google_callback(code: str | None = None, state: str | None = None, error: str | None = None, db: Session = Depends(get_db)):
    if error or not code or not state:
        return frontend_redirect("denied")
    state_row = db.scalar(select(GoogleOAuthState).where(GoogleOAuthState.state_digest == hashlib.sha256(state.encode()).hexdigest()))
    if state_row is None or state_row.used_at is not None or aware(state_row.expires_at) <= now_utc():
        return frontend_redirect("expired")
    state_row.used_at = now_utc()
    db.commit()
    service = state_row.service
    user_id = state_row.user_id
    verifier = state_row.code_verifier
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_response = await client.post(GOOGLE_TOKEN, data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": verifier,
            })
            token_response.raise_for_status()
            token_data = token_response.json()
            access_token = token_data["access_token"]
            user_info_response = await client.get("https://openidconnect.googleapis.com/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
            user_info_response.raise_for_status()
            provider_email = user_info_response.json()["email"]
        account = get_connection(db, user_id, service)
        refresh_token = token_data.get("refresh_token")
        if not refresh_token and account:
            refresh_token = decrypt(account.refresh_token_ciphertext)
        if not refresh_token:
            return frontend_redirect("refresh_token_missing")
        scopes = token_data.get("scope", "").split() or BASE_SCOPES + SERVICE_SCOPES[service]
        if account is None:
            account = ConnectedAccount(user_id=user_id, provider=service, provider_email=provider_email, access_token_ciphertext=encrypt(access_token), refresh_token_ciphertext=encrypt(refresh_token), scopes=scopes, access_token_expires_at=now_utc() + timedelta(seconds=int(token_data.get("expires_in", 3600))), status="connected")
            db.add(account)
        else:
            account.provider_email = provider_email
            account.access_token_ciphertext = encrypt(access_token)
            account.refresh_token_ciphertext = encrypt(refresh_token)
            account.scopes = scopes
            account.access_token_expires_at = now_utc() + timedelta(seconds=int(token_data.get("expires_in", 3600)))
            account.status = "connected"
        db.commit()
        return frontend_redirect("connected")
    except (httpx.HTTPError, KeyError, ValueError):
        db.rollback()
        return frontend_redirect("failed")


async def usable_access_token(account: ConnectedAccount, db: Session) -> str:
    expiry = aware(account.access_token_expires_at)
    if expiry > now_utc() + timedelta(seconds=60):
        return decrypt(account.access_token_ciphertext)
    refresh = decrypt(account.refresh_token_ciphertext)
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(GOOGLE_TOKEN, data={"client_id": settings.google_client_id, "client_secret": settings.google_client_secret, "refresh_token": refresh, "grant_type": "refresh_token"})
    if response.is_error:
        account.status = "needs_attention"
        db.commit()
        raise HTTPException(status_code=502, detail="Google authorization expired or was revoked. Reconnect this account.")
    result = response.json()
    account.access_token_ciphertext = encrypt(result["access_token"])
    account.access_token_expires_at = now_utc() + timedelta(seconds=int(result.get("expires_in", 3600)))
    db.commit()
    return result["access_token"]


def classify_subject(subject: str) -> str:
    text = subject.casefold()
    if any(term in text for term in ["interview", "schedule a call", "phone screen"]):
        return "interview"
    if any(term in text for term in ["assessment", "coding challenge", "online test"]):
        return "assessment"
    if any(term in text for term in ["offer", "congratulations"]):
        return "offer"
    if any(term in text for term in ["not moving forward", "unfortunately", "rejection"]):
        return "rejection"
    if any(term in text for term in ["application received", "application submitted", "thank you for applying"]):
        return "application_confirmation"
    return "other"


@router.post("/gmail/sync")
async def sync_gmail(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    account = get_connection(db, user.id, "gmail")
    if account is None or account.status != "connected":
        raise HTTPException(status_code=409, detail="Connect Gmail before syncing")
    token = await usable_access_token(account, db)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=20) as client:
        listing = await client.get(f"{GMAIL_API}/messages", headers=headers, params={"maxResults": 50})
        if listing.is_error:
            raise HTTPException(status_code=502, detail="Gmail could not be synchronized. Check the connection and try again.")
        messages = listing.json().get("messages", [])
        imported = 0
        for item in messages:
            existing = db.scalar(select(EmailEvent.id).where(EmailEvent.user_id == user.id, EmailEvent.provider_message_id == item["id"]))
            if existing:
                continue
            response = await client.get(f"{GMAIL_API}/messages/{item['id']}", headers=headers, params=[("format", "metadata"), ("metadataHeaders", "Subject"), ("metadataHeaders", "From"), ("fields", "id,threadId,internalDate,payload(headers)")])
            if response.is_error:
                continue
            data = response.json()
            fields = {header.get("name", "").casefold(): header.get("value", "") for header in data.get("payload", {}).get("headers", [])}
            received_at = datetime.fromtimestamp(int(data["internalDate"]) / 1000, tz=timezone.utc) if data.get("internalDate") else None
            db.add(EmailEvent(user_id=user.id, provider_message_id=data["id"], thread_id=data.get("threadId"), sender=fields.get("from", "")[:500], subject=fields.get("subject", "")[:1000], received_at=received_at, classification=classify_subject(fields.get("subject", ""))))
            imported += 1
        account.last_synced_at = now_utc()
        account.status = "connected"
        db.commit()
    return {"checked": len(messages), "new_events": imported}


@router.get("/gmail/events")
def gmail_events(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    events = db.scalars(select(EmailEvent).where(EmailEvent.user_id == user.id).order_by(EmailEvent.received_at.desc().nullslast(), EmailEvent.id.desc()).limit(100)).all()
    return [{"id": e.id, "sender": e.sender, "subject": e.subject, "received_at": e.received_at, "classification": e.classification, "reviewed": e.reviewed} for e in events]


@router.post("/gmail/events/{event_id}/confirm")
def confirm_gmail_event(event_id: int, application_id: int, new_status: str = Query(), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if new_status not in APPLICATION_STATUSES:
        raise HTTPException(status_code=422, detail="Unknown application status")
    event = db.scalar(select(EmailEvent).where(EmailEvent.id == event_id, EmailEvent.user_id == user.id))
    application = db.scalar(select(Application).where(Application.id == application_id, Application.user_id == user.id))
    if event is None or application is None:
        raise HTTPException(status_code=404, detail="Email event or application not found")
    previous = application.status
    application.status = new_status
    db.add(ApplicationEvent(application_id=application.id, previous_status=previous, new_status=new_status, note=f"Confirmed from Gmail: {event.subject or '(no subject)'} — {event.sender or 'unknown sender'}", source="gmail_user_confirmed"))
    event.reviewed = True
    db.commit()
    return {"status": new_status, "reviewed": True}


@router.post("/calendar/sync")
async def sync_calendar(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    account = get_connection(db, user.id, "calendar")
    if account is None or account.status != "connected":
        raise HTTPException(status_code=409, detail="Connect Google Calendar before syncing")
    token = await usable_access_token(account, db)
    start = now_utc() - timedelta(days=30)
    end = now_utc() + timedelta(days=90)
    params = {"timeMin": start.isoformat(), "timeMax": end.isoformat(), "maxResults": 100, "singleEvents": "true", "orderBy": "startTime", "fields": "items(id,summary,start,end,organizer(email),updated)"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(CALENDAR_API, headers={"Authorization": f"Bearer {token}"}, params=params)
    if response.is_error:
        raise HTTPException(status_code=502, detail="Google Calendar could not be synchronized. Check the connection and try again.")
    items = response.json().get("items", [])
    imported = 0
    for item in items:
        start_value = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
        if not start_value:
            continue
        starts_at = datetime.fromisoformat(start_value.replace("Z", "+00:00"))
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=timezone.utc)
        end_value = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
        ends_at = datetime.fromisoformat(end_value.replace("Z", "+00:00")) if end_value else None
        organizer = item.get("organizer", {}).get("email")
        event = db.scalar(select(CalendarEvent).where(CalendarEvent.user_id == user.id, CalendarEvent.provider_event_id == item["id"]))
        if event is None:
            db.add(CalendarEvent(user_id=user.id, provider_event_id=item["id"], summary=(item.get("summary") or "Calendar event")[:500], organizer=organizer, starts_at=starts_at, ends_at=ends_at))
            imported += 1
        else:
            event.summary = (item.get("summary") or "Calendar event")[:500]
            event.organizer = organizer
            event.starts_at = starts_at
            event.ends_at = ends_at
    account.last_synced_at = now_utc()
    db.commit()
    return {"checked": len(items), "new_events": imported}


@router.get("/calendar/events")
def calendar_events(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(CalendarEvent).where(CalendarEvent.user_id == user.id).order_by(CalendarEvent.starts_at).limit(200)).all()
    return [{"id": event.id, "summary": event.summary, "organizer": event.organizer, "starts_at": event.starts_at, "ends_at": event.ends_at} for event in rows]


@router.delete("/{service}")
async def disconnect_account(service: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if service not in SERVICE_SCOPES:
        raise HTTPException(status_code=404, detail="Unknown Google integration")
    account = get_connection(db, user.id, service)
    if account is None:
        return {"disconnected": True}
    token = decrypt(account.refresh_token_ciphertext)
    async with httpx.AsyncClient(timeout=10) as client:
        revoke = await client.post("https://oauth2.googleapis.com/revoke", data={"token": token})
    if revoke.is_error and revoke.status_code != 400:
        account.status = "revoke_pending"
        db.commit()
        raise HTTPException(status_code=502, detail="Google revocation failed. Retry disconnect so access can be revoked.")
    db.delete(account)
    if service == "gmail":
        db.query(EmailEvent).filter(EmailEvent.user_id == user.id).delete(synchronize_session=False)
    else:
        db.query(CalendarEvent).filter(CalendarEvent.user_id == user.id).delete(synchronize_session=False)
    db.commit()
    return {"disconnected": True}
