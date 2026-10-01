from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MealTimeItem(BaseModel):
    name: str # Breakfast, Lunch, Dinner, Snack
    start: str # "08:00"
    end: str   # "08:30"

class CommitmentItem(BaseModel):
    title: str # "Family time", "Chores", "Sports"
    start: str # "18:00"
    end: str   # "19:00"

class AvailabilitySchema(BaseModel):
    day_of_week: Optional[str] = "all"
    wake_time: str = Field(default="07:00", description="HH:MM")
    sleep_time: str = Field(default="23:00", description="HH:MM")
    
    college_start: str = Field(default="09:00", description="HH:MM")
    college_end: str = Field(default="16:00", description="HH:MM")
    
    morning_travel_minutes: int = Field(default=30, ge=0, le=180)
    evening_travel_minutes: int = Field(default=30, ge=0, le=180)
    
    meals: List[MealTimeItem] = Field(default_factory=lambda: [
        MealTimeItem(name="Breakfast", start="08:00", end="08:30"),
        MealTimeItem(name="Lunch", start="13:00", end="13:45"),
        MealTimeItem(name="Dinner", start="20:00", end="20:45")
    ])
    
    exercise_minutes: int = Field(default=30, ge=0, le=120)
    exercise_time: str = Field(default="07:30")
    
    commitments: List[CommitmentItem] = Field(default_factory=list)
    
    available_study_hours: float = Field(default=3.0, ge=0.5, le=12.0)
    preferred_study_time: str = Field(default="evening") # morning, afternoon, evening, night
    session_duration_minutes: int = Field(default=45, ge=15, le=120)
    break_duration_minutes: int = Field(default=10, ge=5, le=30)

class AvailabilityResponse(AvailabilitySchema):
    id: str
    user_id: str
    balance_summary: Optional[Dict[str, Any]] = None # Calculated 9-8-7 balance (Sleep, Work, Personal/Study)

    class Config:
        from_attributes = True
