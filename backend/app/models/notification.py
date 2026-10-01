from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Notification:
    user_id: str
    title: str
    message: str
    type: str = "info"  # session_start | upcoming | break_start | break_end | checkpoint | warning
    is_read: bool = False
    created_at: datetime = field(default_factory=_now)
    id: Optional[str] = None


@dataclass
class AIRecommendation:
    user_id: str
    recommendation_text: str
    category: str = "Topic Focus"     # Topic Focus | Schedule Balance | Exam Urgency | Adaptive Learning
    topic: Optional[str] = None
    priority: str = "High"            # High | Medium | Low
    is_dismissed: bool = False
    created_at: datetime = field(default_factory=_now)
    id: Optional[str] = None
