from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CheckpointQuestionPublic(BaseModel):
    question_id: str
    question: str
    options: List[str]

class CheckpointPublicResponse(BaseModel):
    checkpoint_id: str
    study_session_id: Optional[str] = None
    subject_id: str
    subject_name: str
    topic: str
    total_questions: int
    questions: List[CheckpointQuestionPublic]

class CheckpointAnswerSubmission(BaseModel):
    question_id: str
    selected_answer: str

class CheckpointSubmitRequest(BaseModel):
    answers: List[CheckpointAnswerSubmission]

class CheckpointAnswerReview(BaseModel):
    question_id: str
    question: str
    options: List[str]
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: Optional[str] = None

class CheckpointResultResponse(BaseModel):
    checkpoint_id: str
    subject_name: str
    topic: str
    score: int
    total_questions: int
    percentage: float
    status: str
    reviews: List[CheckpointAnswerReview]
    topic_level_updated: str # e.g. "Improved from 45% to 75% (Strong)"
    adaptive_recommendation: str
    completed_at: Optional[datetime] = None
