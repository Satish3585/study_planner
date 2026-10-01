from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Availability:
    user_id: str
    day_of_week: str = "all"

    wake_time: str = "07:00"
    sleep_time: str = "23:00"

    college_start: str = "09:00"
    college_end: str = "16:00"

    morning_travel_minutes: int = 30
    evening_travel_minutes: int = 30

    # Stored as JSON string, deserialized on the fly
    meal_times_json: str = '[{"name":"Breakfast","start":"08:00","end":"08:30"},{"name":"Lunch","start":"13:00","end":"13:45"},{"name":"Dinner","start":"20:00","end":"20:45"}]'
    exercise_minutes: int = 30
    exercise_time: str = "07:30"

    commitments_json: str = "[]"

    available_study_hours: float = 3.0
    preferred_study_time: str = "evening"
    session_duration_minutes: int = 45
    break_duration_minutes: int = 10

    updated_at: datetime = field(default_factory=_now)
    id: Optional[str] = None
