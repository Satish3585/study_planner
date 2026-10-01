from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Checkpoint:
    user_id: str
    subject_id: str
    topic: str

    study_session_id: Optional[str] = None
    total_questions: int = 3
    score: int = 0
    percentage: float = 0.0

    # Embedded questions list (stored inside checkpoint document)
    questions: List[dict] = field(default_factory=list)

    # Status: generated | completed
    status: str = "generated"

    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=_now)
    id: Optional[str] = None


@dataclass
class CheckpointAnswer:
    checkpoint_id: str
    question_id: str
    selected_answer: Optional[str] = None
    is_correct: bool = False
    created_at: datetime = field(default_factory=_now)
    id: Optional[str] = None
