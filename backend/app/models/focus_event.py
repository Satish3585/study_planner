from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FocusEvent:
    user_id: str
    event_type: str  # TAB_SWITCH | WINDOW_BLUR | FULLSCREEN_EXIT | COPY_ATTEMPT | PASTE_ATTEMPT | RIGHT_CLICK | INACTIVITY

    study_session_id: Optional[str] = None
    assessment_id: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime = field(default_factory=_now)
    id: Optional[str] = None
