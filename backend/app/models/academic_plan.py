from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AcademicPlan:
    user_id: str
    title: str = "Personalized Academic Plan"
    status: str = "active"  # active | archived | completed
    total_allocated_hours: float = 0.0

    allocation_ratio_json: str = '{"weak_ratio": 0.60, "moderate_ratio": 0.30, "strong_ratio": 0.10}'
    topics_plan_json: Optional[str] = None

    generated_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    id: Optional[str] = None
