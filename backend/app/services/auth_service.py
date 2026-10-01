from __future__ import annotations
from typing import Optional, Tuple
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.mongo import doc_to_dict, model_to_doc, oid
from app.services.otp_service import OTPService


def _doc_to_user(doc: dict) -> Optional[User]:
    if not doc:
        return None
    d = doc_to_dict(doc)
    return User(
        id=d.get("id"),
        full_name=d["full_name"],
        age=d["age"],
        class_grade=d["class_grade"],
        course=d["course"],
        semester=d["semester"],
        hashed_password=d["hashed_password"],
        email=d.get("email"),
        mobile=d.get("mobile"),
        is_verified=d.get("is_verified", False),
        is_active=d.get("is_active", True),
        otp_hash=d.get("otp_hash"),
        otp_expires_at=d.get("otp_expires_at"),
        otp_attempts=d.get("otp_attempts", 0),
        otp_last_sent_at=d.get("otp_last_sent_at"),
        created_at=d.get("created_at", datetime.now(timezone.utc)),
        updated_at=d.get("updated_at", datetime.now(timezone.utc)),
    )


class AuthService:
    @staticmethod
    async def register_user(
        payload: RegisterRequest, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[User], str, Optional[str]]:
        # Check duplicate email
        if payload.email:
            existing = await db.users.find_one({"email": payload.email.strip().lower()})
            if existing:
                return None, "An account with this email address already exists.", None

        # Check duplicate mobile
        if payload.mobile:
            existing = await db.users.find_one({"mobile": payload.mobile.strip()})
            if existing:
                return None, "An account with this mobile number already exists.", None

        now = datetime.now(timezone.utc)
        new_user = User(
            full_name=payload.full_name.strip(),
            age=payload.age,
            class_grade=payload.class_grade.strip(),
            course=payload.course.strip(),
            semester=payload.semester.strip(),
            email=payload.email.strip().lower() if payload.email else None,
            mobile=payload.mobile.strip() if payload.mobile else None,
            hashed_password=hash_password(payload.password),
            is_verified=False,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        result = await db.users.insert_one(model_to_doc(new_user))
        new_user.id = str(result.inserted_id)

        # Link subjects
        for sub_name in payload.subjects:
            clean_name = sub_name.strip()
            if not clean_name:
                continue
            # Find or create subject
            subject_doc = await db.subjects.find_one(
                {"name": {"$regex": f"^{clean_name}$", "$options": "i"}}
            )
            if not subject_doc:
                sub_result = await db.subjects.insert_one(
                    {"name": clean_name, "created_at": now}
                )
                subject_id = str(sub_result.inserted_id)
            else:
                subject_id = str(subject_doc["_id"])

            # Upsert user_subject
            await db.user_subjects.update_one(
                {"user_id": new_user.id, "subject_id": subject_id},
                {"$setOnInsert": {
                    "user_id": new_user.id,
                    "subject_id": subject_id,
                    "subject_name": clean_name,
                    "is_active": True,
                    "confidence_level": "Moderate",
                    "created_at": now,
                }},
                upsert=True,
            )

        # Trigger OTP
        success, otp_msg, demo_otp = await OTPService.generate_and_send_otp(new_user, db)
        return new_user, "Registration successful. Please enter the OTP to verify your account.", demo_otp

    @staticmethod
    async def authenticate_user(
        payload: LoginRequest, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[User], str, Optional[str]]:
        ident = payload.identifier.strip().lower()
        doc = await db.users.find_one(
            {"$or": [{"email": ident}, {"mobile": payload.identifier.strip()}]}
        )
        user = _doc_to_user(doc)

        if not user:
            return None, "Invalid email/mobile or password.", None

        if not verify_password(payload.password, user.hashed_password):
            return None, "Invalid email/mobile or password.", None

        if not user.is_verified:
            _, _, demo_otp = await OTPService.generate_and_send_otp(user, db)
            return None, "ACCOUNT_NOT_VERIFIED", demo_otp

        token = create_access_token({"sub": user.id, "email": user.email, "mobile": user.mobile})
        return user, token, None

    @staticmethod
    async def get_user_by_id(user_id: str, db: AsyncIOMotorDatabase) -> Optional[User]:
        try:
            doc = await db.users.find_one({"_id": oid(user_id)})
        except Exception:
            return None
        return _doc_to_user(doc)

    @staticmethod
    async def get_user_by_identifier(identifier: str, db: AsyncIOMotorDatabase) -> Optional[User]:
        ident = identifier.strip().lower()
        doc = await db.users.find_one(
            {"$or": [{"email": ident}, {"mobile": identifier.strip()}]}
        )
        return _doc_to_user(doc)
