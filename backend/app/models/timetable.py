from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TimetableEntry:
    user_id: str
    date: str          # ISO date string "YYYY-MM-DD"
    start_time: str    # "18:30"
    end_time: str      # "19:15"
    duration_minutes: int
    subject_name: str
    topic: str

    academic_plan_id: Optional[str] = None
    subject_id: Optional[str] = None

    activity_type: str = "Study"   # Study | Practice | Revision | Break
    priority: str = "Medium"       # High | Medium | Low
    reason: Optional[str] = None

    # Status: Scheduled | InProgress | Completed | Skipped | Rescheduled
    status: str = "Scheduled"
    missed_reason: Optional[str] = None

    actual_started_at: Optional[datetime] = None
    actual_completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=_now)
    id: Optional[str] = None
