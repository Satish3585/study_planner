from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class AssessmentStartRequest(BaseModel):
    subject_id: str
    duration_minutes: int = Field(default=30, ge=5, le=120)
    question_count: int = Field(default=15, ge=5, le=50) # default 15 for baseline (adaptive, realistic)

class RetestStartRequest(BaseModel):
    subject_id: str
    source_assessment_id: Optional[str] = None
    topic: Optional[str] = None
    duration_minutes: int = Field(default=20, ge=5, le=120)
    question_count: int = Field(default=3, ge=1, le=20)

class RetestStateResponse(BaseModel):
    subject_id: str
    state: str  # available | skipped | reminded | in_progress | completed
    topics: List[str] = []
    assessment_id: Optional[str] = None
    reminder_at: Optional[datetime] = None

class AssessmentQuestionPublic(BaseModel):
    question_id: str
    topic: str
    difficulty: str
    question: str
    options: List[str]

class AssessmentPublicResponse(BaseModel):
    assessment_id: str
    subject_id: str
    subject_name: str
    title: str
    duration_minutes: int
    total_questions: int
    status: str
    started_at: datetime
    expires_at: datetime
    remaining_seconds: int
    questions: List[AssessmentQuestionPublic]

class QuestionAnswerSubmission(BaseModel):
    question_id: str
    selected_answer: str
    time_taken_seconds: Optional[int] = 0

class AssessmentSubmitRequest(BaseModel):
    answers: List[QuestionAnswerSubmission]

class TopicBreakdownItem(BaseModel):
    topic: str
    total: int
    correct: int
    percentage: float
    category: str # Strong, Moderate, Needs Attention
    priority: str # High, Medium, Low
    previous_percentage: Optional[float] = None
    difference: Optional[float] = None
    trend: Optional[str] = None

class AssessmentResultResponse(BaseModel):
    assessment_id: str
    subject_name: str
    status: str
    score: int
    total_questions: int
    percentage: float
    knowledge_level: str # Beginner, Intermediate, Advanced
    anti_cheat_warnings: int
    topic_breakdown: List[TopicBreakdownItem]
    strengths: List[str]
    moderate_topics: List[str]
    weak_topics: List[str]
    priority_topics: List[str]
    recommendations: List[str]
    completed_at: Optional[datetime] = None
    trend: Optional[str] = None
    feedback: List[str] = []

class AntiCheatEventRequest(BaseModel):
    event_type: str # TAB_SWITCH, WINDOW_BLUR, FULLSCREEN_EXIT, COPY_ATTEMPT, PASTE_ATTEMPT, RIGHT_CLICK
    details: Optional[str] = None
