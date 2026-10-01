from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Subject:
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=_now)
    id: Optional[str] = None


@dataclass
class UserSubject:
    user_id: str
    subject_id: str
    subject_name: str
    is_active: bool = True
    confidence_level: str = "Moderate"  # Beginner, Moderate, Confident
    created_at: datetime = field(default_factory=_now)
    id: Optional[str] = None
