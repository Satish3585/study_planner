from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/retest", tags=["Retest"])


@router.get("/weekly/state")
async def weekly_retest_state(
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await AssessmentService.weekly_retest_state(user, db)


@router.post("/weekly/start", status_code=status.HTTP_201_CREATED)
async def start_weekly_retest(
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    assessment, message = await AssessmentService.start_weekly_retest(user, db)
    if not assessment:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message, "assessment_id": assessment.id, "total_questions": assessment.total_questions}


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_daily_retest(
    date_value: str = Query(..., alias="date", description="Study date in YYYY-MM-DD format"),
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        date.fromisoformat(date_value)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD.")

    assessment, message = await AssessmentService.start_daily_retest(user, date_value, db)
    if not assessment:
        raise HTTPException(status_code=400, detail=message)
    return {
        "message": message,
        "assessment_id": assessment.id,
        "total_questions": assessment.total_questions,
        "duration_minutes": assessment.duration_minutes,
        "topics": assessment.retest_topics,
    }
