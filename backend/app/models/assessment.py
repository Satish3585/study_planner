from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Assessment:
    user_id: str
    subject_id: str
    title: str
    assessment_type: str = "baseline"  # baseline | retest
    source_assessment_id: Optional[str] = None
    retest_topics: List[str] = field(default_factory=list)
    retest_metadata: Dict[str, Any] = field(default_factory=dict)
    retest_date: Optional[str] = None
    retest_kind: Optional[str] = None
    duration_minutes: int = 30
    total_questions: int = 30

    # Status: not_started | in_progress | completed | expired
    status: str = "not_started"

    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    score: int = 0
    percentage: float = 0.0
    knowledge_level: str = "Needs Assessment"
    anti_cheat_warnings: int = 0

    # Embedded questions (stored in assessment document)
    questions: List[dict] = field(default_factory=list)
    analysis_json: Optional[str] = None

    created_at: datetime = field(default_factory=_now)
    id: Optional[str] = None


@dataclass
class TopicPerformance:
    user_id: str
    subject_id: str
    topic: str
    score_percentage: float = 0.0
    total_questions: int = 0
    correct_questions: int = 0

    # Knowledge Category: Strong | Moderate | Needs Attention
    knowledge_category: str = "Needs Attention"
    priority_weight: float = 1.0

    last_assessed_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    id: Optional[str] = None
