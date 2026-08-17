import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import (
    AuthMessage, LoginRequest, PasswordChangeRequest, PasswordResetConfirm,
    PasswordResetRequest, RefreshRequest, RegisterRequest, TokenResponse, UserRead,
)
from app.modules.auth.security import hash_password, verify_password, create_access_token
from app.modules.candidates.models import (
    CandidateProfile, Document, EmailVerificationToken, PasswordResetToken, RefreshToken, User,
)
from app.modules.media.models import MediaRecording
from app.modules.media.storage import delete_object
from app.core.config import get_settings
from app.core.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])

def _hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hash_one_time_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

async def _issue_refresh(db: AsyncSession, user: User) -> str:
    s = get_settings()
    raw = secrets.token_urlsafe(48)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=_hash_refresh(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=s.refresh_token_ttl_seconds),
    ))
    return raw

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower()
    if await db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="EMAIL_ALREADY_REGISTERED")
    user = User(email=email, password_hash=hash_password(payload.password))
    user.profile = CandidateProfile(
        first_name=payload.first_name, last_name=payload.last_name,
        domain=payload.domain, target_role=payload.target_role,
        phone=payload.phone, location=payload.location,
    )
    db.add(user)
    verification_token = None
    if get_settings().email_verification_required:
        await db.flush()
        verification_token = secrets.token_urlsafe(48)
        db.add(EmailVerificationToken(
            user_id=user.id,
            token_hash=_hash_one_time_token(verification_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        ))
    await db.commit()
    await db.refresh(user)
    if verification_token:
        send_email(
            recipient=user.email,
            subject="Verify your IARH account",
            body=f"Verify your account: {get_settings().public_app_url}/api/v1/auth/verify-email?token={verification_token}",
        )
    return user

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")
    if get_settings().email_verification_required and not user.email_verified:
        raise HTTPException(status_code=403, detail="EMAIL_VERIFICATION_REQUIRED")
    refresh = await _issue_refresh(db, user)
    await db.commit()
    return TokenResponse(access_token=create_access_token(user.id, user.role.value, user.token_version), refresh_token=refresh)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    row = await db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == _hash_refresh(payload.refresh_token))
        .with_for_update()
    )
    now = datetime.now(timezone.utc)
    if row is None or row.revoked_at is not None or row.expires_at <= now:
        raise HTTPException(status_code=401, detail="INVALID_REFRESH_TOKEN")
    user = await db.get(User, row.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="USER_NOT_FOUND")
    row.revoked_at = now
    new_refresh = await _issue_refresh(db, user)
    await db.commit()
    return TokenResponse(access_token=create_access_token(user.id, user.role.value, user.token_version), refresh_token=new_refresh)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    row = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == _hash_refresh(payload.refresh_token)))
    if row and row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        await db.commit()

@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/verify-email", response_model=AuthMessage)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    row = await db.scalar(select(EmailVerificationToken).where(
        EmailVerificationToken.token_hash == _hash_one_time_token(token),
        EmailVerificationToken.used_at.is_(None),
        EmailVerificationToken.expires_at > datetime.now(timezone.utc),
    ).with_for_update())
    if row is None:
        raise HTTPException(status_code=400, detail="INVALID_OR_EXPIRED_VERIFICATION_TOKEN")
    user = await db.get(User, row.user_id, with_for_update=True)
    if user is None:
        raise HTTPException(status_code=400, detail="INVALID_VERIFICATION_USER")
    user.email_verified = True
    row.used_at = datetime.now(timezone.utc)
    await db.commit()
    return AuthMessage(message="EMAIL_VERIFIED")


@router.post("/change-password", response_model=AuthMessage)
async def change_password(payload: PasswordChangeRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="INVALID_CURRENT_PASSWORD")
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    await db.execute(RefreshToken.__table__.delete().where(RefreshToken.user_id == user.id))
    await db.commit()
    return AuthMessage(message="PASSWORD_CHANGED")


@router.post("/request-password-reset", response_model=AuthMessage)
async def request_password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    debug_token = None
    if user is not None:
        raw_token = secrets.token_urlsafe(48)
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_one_time_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        ))
        await db.commit()
        settings = get_settings()
        if settings.email_delivery_mode == "smtp":
            send_email(
                recipient=user.email,
                subject="Reset your IARH password",
                body=f"Reset your password: {settings.public_app_url}/reset-password?token={raw_token}",
            )
        elif settings.app_env.lower() in {"development", "dev"}:
            debug_token = raw_token
    return AuthMessage(message="IF_ACCOUNT_EXISTS_RESET_WAS_SENT", debug_token=debug_token)


@router.post("/reset-password", response_model=AuthMessage)
async def reset_password(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    row = await db.scalar(select(PasswordResetToken).where(
        PasswordResetToken.token_hash == _hash_one_time_token(payload.token),
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > datetime.now(timezone.utc),
    ).with_for_update())
    if row is None:
        raise HTTPException(status_code=400, detail="INVALID_OR_EXPIRED_RESET_TOKEN")
    user = await db.get(User, row.user_id, with_for_update=True)
    if user is None:
        raise HTTPException(status_code=400, detail="INVALID_RESET_USER")
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    row.used_at = datetime.now(timezone.utc)
    await db.execute(RefreshToken.__table__.delete().where(RefreshToken.user_id == user.id))
    await db.commit()
    return AuthMessage(message="PASSWORD_RESET")


@router.delete("/me/data", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_data(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Delete the account and its stored media. The caller must be authenticated."""
    profile = await db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
    storage_keys: list[str] = []
    if profile is not None:
        recordings = (await db.scalars(select(MediaRecording).where(MediaRecording.candidate_id == profile.id))).all()
        storage_keys.extend(recording.storage_key for recording in recordings if recording.storage_key)
        documents = (await db.scalars(select(Document).where(Document.candidate_id == profile.id))).all()
        storage_keys.extend(document.storage_key for document in documents if document.storage_key)
    await db.delete(user)
    await db.commit()
    for key in storage_keys:
        try:
            delete_object(key)
        except Exception:
            # The account is deleted; an operator can reconcile this orphaned key.
            import logging
            logging.getLogger("iarh.audit").exception("media_cleanup_failed", extra={"storage_key": key})
