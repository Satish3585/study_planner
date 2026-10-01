from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

class AIRecommendationResponse(BaseModel):
    id: str
    recommendation_text: str
    category: str
    topic: Optional[str] = None
    priority: str
    is_dismissed: bool
    created_at: datetime
