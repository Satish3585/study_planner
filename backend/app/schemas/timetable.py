from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field

class TimetableEntryResponse(BaseModel):
    id: str
    date: str
    start_time: str
    end_time: str
    duration_minutes: int
    subject_id: Optional[str] = None
    subject_name: str
    topic: str
    activity_type: str # Study, Practice, Revision, Break
    priority: str      # High, Medium, Low
    reason: Optional[str] = None
    status: str        # Scheduled, InProgress, Completed, Skipped, Rescheduled
    missed_reason: Optional[str] = None
    actual_started_at: Optional[datetime] = None
    actual_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TimetableUpdateRequest(BaseModel):
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    topic: Optional[str] = None
    priority: Optional[str] = None

class TimetableSkipRequest(BaseModel):
    reason: str = Field(..., description="College / Work, Busy, Forgot, Not feeling well, Other")

class TimetableRegenerateRequest(BaseModel):
    days_ahead: int = Field(default=7, ge=1, le=30)
    preserve_completed: bool = True
