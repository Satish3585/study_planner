from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
from app.utils.validators import is_valid_email, is_valid_mobile, validate_password_strength

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=5, le=120)
    class_grade: str = Field(..., min_length=1, max_length=50)
    course: str = Field(..., min_length=1, max_length=100)
    semester: str = Field(..., min_length=1, max_length=50)
    subjects: List[str] = Field(..., min_length=1)
    
    email: Optional[str] = None
    mobile: Optional[str] = None
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(...)

    @model_validator(mode="after")
    def validate_register_fields(self):
        if not self.email and not self.mobile:
            raise ValueError("Either email or mobile number must be provided.")
        
        if self.email and not is_valid_email(self.email):
            raise ValueError("Invalid email format.")
            
        if self.mobile and not is_valid_mobile(self.mobile):
            raise ValueError("Invalid mobile number. Must have 10-15 digits.")
            
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
            
        valid, msg = validate_password_strength(self.password)
        if not valid:
            raise ValueError(msg)
            
        if not self.subjects:
            raise ValueError("At least one subject must be specified.")
            
        return self

class LoginRequest(BaseModel):
    identifier: str # Email or mobile number
    password: str

class SendOTPRequest(BaseModel):
    identifier: str # Email or mobile

class VerifyOTPRequest(BaseModel):
    identifier: str
    otp: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    full_name: str
    age: int
    class_grade: str
    course: str
    semester: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    is_verified: bool
    is_active: bool
    has_completed_assessment: bool = False
    has_completed_availability: bool = False

    class Config:
        from_attributes = True
