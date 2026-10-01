from typing import List, Optional
from pydantic import BaseModel, Field

class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = None
    description: Optional[str] = None

class SubjectCreate(SubjectBase):
    pass

class SubjectResponse(SubjectBase):
    id: str
    is_active: bool = True
    confidence_level: Optional[str] = "Moderate"

    class Config:
        from_attributes = True

class ConfirmSubjectsRequest(BaseModel):
    subjects: List[str] # List of subject names to keep/add
