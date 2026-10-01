from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.schemas.timetable import TimetableEntryResponse

class TopicStatusItem(BaseModel):
    subject: str
    topic: str
    score: float
    category: str # Strong, Moderate, Needs Attention
    priority: str

class TodayProgress(BaseModel):
    total_sessions: int
    completed_sessions: int
    remaining_sessions: int
    percentage: float

class DashboardStatsResponse(BaseModel):
    user_name: str
    today_progress: TodayProgress
    next_session: Optional[TimetableEntryResponse] = None
    strong_topics: List[TopicStatusItem]
    moderate_topics: List[TopicStatusItem]
    needs_attention_topics: List[TopicStatusItem]
    latest_assessment_score: Optional[float] = None
    latest_assessment_subject: Optional[str] = None
    study_streak_days: int
    total_study_minutes: float
    completion_rate_percentage: float
    average_checkpoint_score: float
    ai_insight: str

class SubjectProgressItem(BaseModel):
    subject_id: str
    subject_name: str
    topics_count: int
    strong_count: int
    moderate_count: int
    weak_count: int
    average_score: float
    completed_study_hours: float

class AnalyticsResponse(BaseModel):
    total_study_time_hours: float
    planned_study_time_hours: float
    total_completed_sessions: int
    total_planned_sessions: int
    session_completion_rate: float
    average_checkpoint_accuracy: float
    focus_interruptions_total: int
    current_streak_days: int
    subjects_progress: List[SubjectProgressItem]
    daily_study_breakdown: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]

class AIRecommendationResponse(BaseModel):
    id: str
    category: str
    recommendation_text: str
    topic: Optional[str] = None
    priority: str
    created_at: str

    class Config:
        from_attributes = True
