import os
import secrets
from datetime import datetime, timedelta

import aiosmtplib
from email.message import EmailMessage
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth import create_access_token, hash_password, verify_password
from models import User
from repositories.user_repo import UserRepository

_repo = UserRepository()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
RESET_TOKEN_EXPIRE_HOURS = int(os.getenv("RESET_TOKEN_EXPIRE_HOURS", "1"))


class UserService:

    async def register(self, session: AsyncSession, email: str, password: str) -> User:
        existing = await _repo.get_by_email(session, email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        return await _repo.create(session, email, hash_password(password))

    async def login(self, session: AsyncSession, email: str, password: str) -> str:
        user = await _repo.get_by_email(session, email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account inactive",
            )
        return create_access_token(user.id)

    async def forgot_password(self, session: AsyncSession, email: str) -> None:
        user = await _repo.get_by_email(session, email)
        if not user:
            return  # Don't reveal whether the email is registered
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
        await _repo.save_reset_token(session, token, user.id, expires_at)
        await _send_reset_email(user.email, token)

    async def reset_password(
        self, session: AsyncSession, token: str, new_password: str
    ) -> None:
        rt = await _repo.get_valid_reset_token(session, token)
        if not rt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )
        await _repo.update_password(session, rt.user_id, hash_password(new_password))
        await _repo.delete_reset_token(session, token)


async def _send_reset_email(email: str, token: str) -> None:
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"

    if not SMTP_USERNAME:
        # SMTP not configured — print URL so developers can test locally
        print(f"[auth] SMTP not configured. Reset URL for {email}: {reset_url}")
        return

    msg = EmailMessage()
    msg["Subject"] = "BrokeNoMore — Reset your password"
    msg["From"] = SMTP_FROM
    msg["To"] = email
    msg.set_content(
        f"Click the link below to reset your password "
        f"(expires in {RESET_TOKEN_EXPIRE_HOURS} hour(s)):\n\n"
        f"{reset_url}\n\n"
        "If you did not request a password reset, you can safely ignore this email."
    )
    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
    except Exception as exc:
        # Log but don't raise — don't leak whether the email address exists
        print(f"[auth] Failed to send reset email to {email}: {exc}")
