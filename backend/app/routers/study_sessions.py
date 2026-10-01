from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.study import (
    StudySessionStartRequest, StudySessionActionResponse, FocusEventLogRequest
)
from app.services.study_service import StudyService
from app.utils.mongo import oid

router = APIRouter(prefix="/study-sessions", tags=["Study Sessions"])

@router.post("/start", response_model=StudySessionActionResponse, status_code=status.HTTP_201_CREATED)
async def start_study_session(
    payload: StudySessionStartRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    session, msg = await StudyService.start_session(user, payload, db)
    if not session:
        raise HTTPException(status_code=400, detail=msg)
    
    sub_name = "Subject"
    if session.subject_id:
        sub_doc = await db.subjects.find_one({"_id": oid(session.subject_id)})
        if sub_doc:
            sub_name = sub_doc["name"]
            
    return StudySessionActionResponse(
        id=session.id,
        timetable_entry_id=session.timetable_entry_id,
        subject_id=session.subject_id,
        subject_name=sub_name,
        topic=session.topic,
        objective=session.objective,
        status=session.status,
        scheduled_duration_minutes=session.scheduled_duration_minutes,
        actual_duration_minutes=session.actual_duration_minutes,
        started_at=session.started_at,
        paused_at=session.paused_at,
        ended_at=session.ended_at,
        focus_score=session.focus_score,
        interruption_count=session.interruption_count,
        completion_percentage=session.completion_percentage,
        partial_completion=session.partial_completion
    )

@router.post("/{session_id}/pause", response_model=StudySessionActionResponse)
async def pause_study_session(
    session_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    session, msg = await StudyService.pause_session(session_id, user.id, db)
    if not session:
        raise HTTPException(status_code=404, detail=msg)
    
    sub_name = "Subject"
    if session.subject_id:
        sub_doc = await db.subjects.find_one({"_id": oid(session.subject_id)})
        if sub_doc:
            sub_name = sub_doc["name"]
            
    return StudySessionActionResponse(
        id=session.id, timetable_entry_id=session.timetable_entry_id,
        subject_id=session.subject_id, subject_name=sub_name,
        topic=session.topic, objective=session.objective, status=session.status,
        scheduled_duration_minutes=session.scheduled_duration_minutes,
        actual_duration_minutes=session.actual_duration_minutes,
        started_at=session.started_at, paused_at=session.paused_at,
        ended_at=session.ended_at, focus_score=session.focus_score,
        interruption_count=session.interruption_count,
        completion_percentage=session.completion_percentage,
        partial_completion=session.partial_completion
    )

@router.post("/{session_id}/resume", response_model=StudySessionActionResponse)
async def resume_study_session(
    session_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    session, msg = await StudyService.resume_session(session_id, user.id, db)
    if not session:
        raise HTTPException(status_code=404, detail=msg)
    
    sub_name = "Subject"
    if session.subject_id:
        sub_doc = await db.subjects.find_one({"_id": oid(session.subject_id)})
        if sub_doc:
            sub_name = sub_doc["name"]
            
    return StudySessionActionResponse(
        id=session.id, timetable_entry_id=session.timetable_entry_id,
        subject_id=session.subject_id, subject_name=sub_name,
        topic=session.topic, objective=session.objective, status=session.status,
        scheduled_duration_minutes=session.scheduled_duration_minutes,
        actual_duration_minutes=session.actual_duration_minutes,
        started_at=session.started_at, paused_at=session.paused_at,
        ended_at=session.ended_at, focus_score=session.focus_score,
        interruption_count=session.interruption_count,
        completion_percentage=session.completion_percentage,
        partial_completion=session.partial_completion
    )

@router.post("/{session_id}/finish", response_model=StudySessionActionResponse)
async def finish_study_session(
    session_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    session, msg = await StudyService.finish_session(session_id, user.id, db)
    if not session:
        raise HTTPException(status_code=404, detail=msg)
    
    sub_name = "Subject"
    if session.subject_id:
        sub_doc = await db.subjects.find_one({"_id": oid(session.subject_id)})
        if sub_doc:
            sub_name = sub_doc["name"]
            
    return StudySessionActionResponse(
        id=session.id, timetable_entry_id=session.timetable_entry_id,
        subject_id=session.subject_id, subject_name=sub_name,
        topic=session.topic, objective=session.objective, status=session.status,
        scheduled_duration_minutes=session.scheduled_duration_minutes,
        actual_duration_minutes=session.actual_duration_minutes,
        started_at=session.started_at, paused_at=session.paused_at,
        ended_at=session.ended_at, focus_score=session.focus_score,
        interruption_count=session.interruption_count,
        completion_percentage=session.completion_percentage,
        partial_completion=session.partial_completion
    )

@router.post("/{session_id}/focus-event")
async def log_focus_event(
    session_id: str,
    payload: FocusEventLogRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    session, interruptions = await StudyService.log_focus_event(
        session_id=session_id,
        user_id=user.id,
        event_type=payload.event_type,
        details=payload.details,
        db=db
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {
        "message": "Focus interruption recorded softly.",
        "interruption_count": interruptions,
        "current_focus_score": session.focus_score
    }
