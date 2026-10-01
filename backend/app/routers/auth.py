from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest, LoginRequest, SendOTPRequest, VerifyOTPRequest,
    TokenResponse, UserResponse
)
from app.services.auth_service import AuthService
from app.services.otp_service import OTPService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    user, msg, demo_otp = await AuthService.register_user(payload, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    
    resp_data = {
        "message": msg,
        "user_id": user.id,
        "identifier": user.email or user.mobile,
        "is_verified": user.is_verified
    }
    if demo_otp:
        resp_data["demo_otp"] = demo_otp
    return resp_data

@router.post("/send-otp")
async def send_otp(payload: SendOTPRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await AuthService.get_user_by_identifier(payload.identifier, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    success, msg, demo_otp = await OTPService.generate_and_send_otp(user, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=msg)

    resp_data = {"message": msg}
    if demo_otp:
        resp_data["demo_otp"] = demo_otp
    return resp_data

@router.post("/verify-otp")
async def verify_otp(payload: VerifyOTPRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await AuthService.get_user_by_identifier(payload.identifier, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    success, msg = await OTPService.verify_otp(user, payload.otp, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    from app.utils.security import create_access_token
    token = create_access_token({"sub": str(user.id), "email": user.email, "mobile": user.mobile})

    return {
        "message": "Account verified successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "mobile": user.mobile,
            "is_verified": True
        }
    }

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    user, result, demo_otp = await AuthService.authenticate_user(payload, db)
    
    if result == "ACCOUNT_NOT_VERIFIED":
        resp_detail = {"message": "Account is not verified. A verification code has been dispatched."}
        if demo_otp:
            resp_detail["demo_otp"] = demo_otp
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=resp_detail)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result)

    has_asmt = await db.assessments.find_one({"user_id": user.id, "status": "completed"}) is not None
    has_avail = await db.availability.find_one({"user_id": user.id}) is not None

    return TokenResponse(
        access_token=result,
        token_type="bearer",
        user={
            "id": user.id,
            "full_name": user.full_name,
            "age": user.age,
            "class_grade": user.class_grade,
            "course": user.course,
            "semester": user.semester,
            "email": user.email,
            "mobile": user.mobile,
            "is_verified": user.is_verified,
            "has_completed_assessment": has_asmt,
            "has_completed_availability": has_avail
        }
    )

@router.get("/me")
async def get_me(user: User = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    has_asmt = await db.assessments.find_one({"user_id": user.id, "status": "completed"}) is not None
    has_avail = await db.availability.find_one({"user_id": user.id}) is not None

    return {
        "id": user.id,
        "full_name": user.full_name,
        "age": user.age,
        "class_grade": user.class_grade,
        "course": user.course,
        "semester": user.semester,
        "email": user.email,
        "mobile": user.mobile,
        "is_verified": user.is_verified,
        "has_completed_assessment": has_asmt,
        "has_completed_availability": has_avail
    }
