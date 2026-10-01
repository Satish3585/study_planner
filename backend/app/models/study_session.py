from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StudySession:
    user_id: str
    topic: str

    timetable_entry_id: Optional[str] = None
    subject_id: Optional[str] = None

    objective: Optional[str] = None
    scheduled_duration_minutes: int = 45
    actual_duration_minutes: float = 0.0

    # Status: started | paused | resumed | completed | abandoned
    status: str = "started"

    started_at: datetime = field(default_factory=_now)
    active_started_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    focus_score: float = 100.0
    interruption_count: int = 0
    completion_percentage: float = 0.0
    partial_completion: bool = False

    id: Optional[str] = None
