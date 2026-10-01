from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class StudySessionStartRequest(BaseModel):
    timetable_entry_id: Optional[str] = None
    subject_id: Optional[str] = None
    topic: Optional[str] = None
    objective: Optional[str] = None
    duration_minutes: Optional[int] = 45

class StudySessionActionResponse(BaseModel):
    id: str
    timetable_entry_id: Optional[str] = None
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    topic: str
    objective: Optional[str] = None
    status: str
    scheduled_duration_minutes: int
    actual_duration_minutes: float
    started_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    focus_score: float
    interruption_count: int
    completion_percentage: float = 0.0
    partial_completion: bool = False

    class Config:
        from_attributes = True

class FocusEventLogRequest(BaseModel):
    event_type: str # TAB_SWITCH, WINDOW_BLUR, FULLSCREEN_EXIT, COPY_ATTEMPT, PASTE_ATTEMPT, RIGHT_CLICK, INACTIVITY
    details: Optional[str] = None
