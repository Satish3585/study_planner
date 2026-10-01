import asyncio
import logging
import smtplib
from email.message import EmailMessage
import httpx
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import User
from app.utils.security import generate_otp, hash_otp, verify_otp_hash
from app.utils.mongo import oid
from app.config import settings

logger = logging.getLogger("study_planner.otp")


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Treat MongoDB's naive UTC datetimes as timezone-aware UTC values."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


async def _send_email(to: str, otp: str) -> bool:
    if not (settings.SMTP_HOST and settings.SMTP_USER):
        return False
    msg = EmailMessage()
    msg["Subject"] = "Your AI Study Planner verification code"
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to
    msg.set_content(
        f"Your verification code is {otp}. It is valid for {settings.OTP_EXPIRY_SECONDS // 60} minutes."
    )

    def _send():
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)

    try:
        await asyncio.to_thread(_send)
        return True
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        return False


async def _send_sms(mobile: str, otp: str) -> bool:
    if settings.SMS_PROVIDER != "fast2sms" or not settings.FAST2SMS_API_KEY:
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://www.fast2sms.com/dev/bulkV2",
                headers={"authorization": settings.FAST2SMS_API_KEY},
                json={"route": "otp", "variables_values": otp, "numbers": mobile[-10:]},
            )
            return r.status_code == 200 and r.json().get("return") is True
    except Exception as e:
        logger.error(f"SMS send failed: {e}")
        return False


class OTPService:
    @staticmethod
    async def generate_and_send_otp(
        user: User, db: AsyncIOMotorDatabase
    ) -> Tuple[bool, str, Optional[str]]:
        """Generates a secure OTP, stores hash, handles cooldown."""
        now = datetime.now(timezone.utc)

        last_sent_at = _as_utc(user.otp_last_sent_at)
        if last_sent_at:
            cooldown_expiry = last_sent_at + timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SECONDS)
            if now < cooldown_expiry:
                remaining = int((cooldown_expiry - now).total_seconds())
                return False, f"Please wait {remaining} seconds before requesting a new OTP.", None

        otp = generate_otp(6)
        otp_hash = hash_otp(otp)
        otp_expires_at = now + timedelta(seconds=settings.OTP_EXPIRY_SECONDS)

        # Persist OTP state to MongoDB
        await db.users.update_one(
            {"_id": oid(user.id)},
            {"$set": {
                "otp_hash": otp_hash,
                "otp_expires_at": otp_expires_at,
                "otp_attempts": 0,
                "otp_last_sent_at": now,
            }},
        )

        # Update local object too (in-memory)
        user.otp_hash = otp_hash
        user.otp_expires_at = otp_expires_at
        user.otp_attempts = 0
        user.otp_last_sent_at = now

        target = user.email or user.mobile or "User"

        if settings.OTP_DEMO_MODE:
            logger.info("=" * 50)
            logger.info(f"🔑 [DEMO OTP] For {target}: {otp} (Valid for {settings.OTP_EXPIRY_SECONDS}s)")
            logger.info("=" * 50)
            # Keep the console output ASCII-only so demo mode also works with
            # Windows terminals using the cp1252 encoding.
            print("\n==========================================")
            print(f"[DEMO OTP] For {target}: {otp}")
            print("==========================================\n")
            return True, "OTP sent successfully.", otp

        sent = False
        if user.email:
            sent = await _send_email(user.email, otp)
        if not sent and user.mobile:
            sent = await _send_sms(user.mobile, otp)
        if not sent:
            logger.error(f"OTP delivery failed for {target}.")
            return False, "Could not deliver the OTP right now. Please try again shortly.", None
        return True, "OTP sent successfully.", None

    @staticmethod
    async def verify_otp(
        user: User, otp_input: str, db: AsyncIOMotorDatabase
    ) -> Tuple[bool, str]:
        """Validates provided OTP against hashed OTP."""
        now = datetime.now(timezone.utc)

        expires_at = _as_utc(user.otp_expires_at)
        if not user.otp_hash or not expires_at:
            return False, "No active OTP found. Please request a new one."

        if now > expires_at:
            await db.users.update_one(
                {"_id": oid(user.id)},
                {"$set": {"otp_hash": None}},
            )
            return False, "OTP has expired. Please request a new code."

        if user.otp_attempts >= settings.OTP_MAX_ATTEMPTS:
            await db.users.update_one(
                {"_id": oid(user.id)},
                {"$set": {"otp_hash": None}},
            )
            return False, "Maximum verification attempts exceeded. Please request a new OTP."

        new_attempts = user.otp_attempts + 1
        await db.users.update_one(
            {"_id": oid(user.id)},
            {"$set": {"otp_attempts": new_attempts}},
        )
        user.otp_attempts = new_attempts

        if not verify_otp_hash(otp_input.strip(), user.otp_hash):
            remaining = max(0, settings.OTP_MAX_ATTEMPTS - new_attempts)
            return False, f"Invalid OTP. {remaining} attempts remaining."

        # Success — activate user
        await db.users.update_one(
            {"_id": oid(user.id)},
            {"$set": {
                "is_verified": True,
                "otp_hash": None,
                "otp_expires_at": None,
                "otp_attempts": 0,
            }},
        )
        user.is_verified = True
        user.otp_hash = None
        user.otp_expires_at = None
        user.otp_attempts = 0

        return True, "Account successfully verified."
