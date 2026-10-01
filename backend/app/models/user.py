"""
MongoDB document models using Python dataclasses.
Each class mirrors a MongoDB collection document.
_id is always stored as a BSON ObjectId; .id is a str representation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class User:
    full_name: str
    age: int
    class_grade: str
    course: str
    semester: str
    hashed_password: str

    email: Optional[str] = None
    mobile: Optional[str] = None

    is_verified: bool = False
    is_active: bool = True

    # OTP state
    otp_hash: Optional[str] = None
    otp_expires_at: Optional[datetime] = None
    otp_attempts: int = 0
    otp_last_sent_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    # Populated from MongoDB after insert
    id: Optional[str] = None
