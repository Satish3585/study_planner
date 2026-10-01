from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.timetable import (
    TimetableEntryResponse, TimetableUpdateRequest, TimetableSkipRequest, TimetableRegenerateRequest
)
from app.services.timetable_service import TimetableService
from app.services.planning_service import PlanningService

router = APIRouter(prefix="/timetable", tags=["Timetable"])

@router.get("", response_model=List[TimetableEntryResponse])
async def get_timetable(
    target_date: Optional[str] = Query(None, description="Filter by YYYY-MM-DD"),
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    parsed_date = None
    if target_date:
        try:
            parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    entries = await TimetableService.get_user_timetable(user.id, parsed_date, db)
    return [
        TimetableEntryResponse(
            id=e.get("id"),
            date=e.get("date"),
            start_time=e.get("start_time"),
            end_time=e.get("end_time"),
            duration_minutes=e.get("duration_minutes"),
            subject_id=e.get("subject_id"),
            subject_name=e.get("subject_name"),
            topic=e.get("topic"),
            activity_type=e.get("activity_type"),
            priority=e.get("priority"),
            reason=e.get("reason"),
            status=e.get("status"),
            missed_reason=e.get("missed_reason"),
            actual_started_at=e.get("actual_started_at"),
            actual_completed_at=e.get("actual_completed_at")
        ) for e in entries
    ]

@router.post("/regenerate")
async def regenerate_timetable(
    payload: TimetableRegenerateRequest = TimetableRegenerateRequest(),
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    result = await PlanningService.generate_plan_and_timetable(
        user, days_ahead=payload.days_ahead, preserve_completed=payload.preserve_completed, db=db
    )
    return {
        "message": f"Timetable regenerated successfully for the next {payload.days_ahead} days.",
        **result
    }

@router.put("/{entry_id}", response_model=TimetableEntryResponse)
async def update_entry(
    entry_id: str,
    payload: TimetableUpdateRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    entry, msg = await TimetableService.update_entry(entry_id, user.id, payload, db)
    if not entry:
        raise HTTPException(status_code=404, detail=msg)
    return TimetableEntryResponse(**entry)

@router.post("/{entry_id}/skip", response_model=TimetableEntryResponse)
async def skip_entry(
    entry_id: str,
    payload: TimetableSkipRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    entry, msg = await TimetableService.skip_entry(entry_id, user.id, payload, db)
    if not entry:
        raise HTTPException(status_code=404, detail=msg)
    return TimetableEntryResponse(**entry)

@router.post("/{entry_id}/complete", response_model=TimetableEntryResponse)
async def complete_entry(
    entry_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    entry, msg = await TimetableService.complete_entry(entry_id, user.id, db)
    if not entry:
        raise HTTPException(status_code=404, detail=msg)
    return TimetableEntryResponse(**entry)
