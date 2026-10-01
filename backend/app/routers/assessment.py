import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.assessment import (
    AssessmentStartRequest, AssessmentPublicResponse, AssessmentQuestionPublic,
    AssessmentSubmitRequest, AssessmentResultResponse, AntiCheatEventRequest
    , RetestStartRequest, RetestStateResponse
)
from app.services.assessment_service import AssessmentService
from app.utils.mongo import as_utc, oid

router = APIRouter(prefix="/assessment", tags=["Assessment"])

@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_assessment(
    payload: AssessmentStartRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    assessment, msg = await AssessmentService.start_assessment(user, payload, db)
    if not assessment:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": msg, "assessment_id": assessment.id}

@router.post("/retest/start", status_code=status.HTTP_201_CREATED)
async def start_retest(
    payload: RetestStartRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    assessment, msg = await AssessmentService.start_retest(user, payload, db)
    if not assessment:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "assessment_id": assessment.id, "topics": assessment.retest_topics}

@router.get("/retest/{subject_id}/state", response_model=RetestStateResponse)
async def get_retest_state(
    subject_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    return await AssessmentService.retest_state(user, subject_id, db)

@router.post("/retest/{subject_id}/skip", response_model=RetestStateResponse)
async def skip_retest(
    subject_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    state = await AssessmentService.retest_state(user, subject_id, db)
    await db.assessments.update_many(
        {"user_id": user.id, "subject_id": subject_id, "assessment_type": "retest", "status": "in_progress"},
        {"$set": {"status": "skipped", "retest_metadata.state": "skipped", "completed_at": datetime.now(timezone.utc)}},
    )
    await db.retest_states.update_one(
        {"user_id": user.id, "subject_id": subject_id},
        {"$set": {"user_id": user.id, "subject_id": subject_id, "state": "skipped", "topics": state.get("topics", [])}},
        upsert=True,
    )
    state["state"] = "skipped"
    return state

@router.post("/retest/{subject_id}/remind", response_model=RetestStateResponse)
async def remind_retest(
    subject_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    state = await AssessmentService.retest_state(user, subject_id, db)
    reminder_at = datetime.now(timezone.utc)
    await db.retest_states.update_one(
        {"user_id": user.id, "subject_id": subject_id},
        {"$set": {"user_id": user.id, "subject_id": subject_id, "state": "reminded", "reminder_at": reminder_at}},
        upsert=True,
    )
    state.update({"state": "reminded", "reminder_at": reminder_at})
    return state

@router.get("/summary")
async def assessment_summary(
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    subs_cursor = db.user_subjects.find({"user_id": user.id, "is_active": True})
    now = datetime.now(timezone.utc)
    out = []
    
    async for us in subs_cursor:
        sub_id = us["subject_id"]
        sub_doc = await db.subjects.find_one({"_id": oid(sub_id)})
        sub_name = sub_doc["name"] if sub_doc else "Unknown"
        
        asmts = await db.assessments.find(
            {"user_id": user.id, "subject_id": sub_id}
        ).sort("completed_at", -1).to_list(None)
        
        completed = next((a for a in asmts if a.get("status") == "completed"), None)
        active = next((a for a in asmts if a.get("status") == "in_progress" and as_utc(a.get("expires_at")) and as_utc(a.get("expires_at")) > now), None)
        
        out.append({
            "subject_id": sub_id, "subject_name": sub_name,
            "status": "completed" if completed else ("in_progress" if active else "pending"),
            "completed_assessment_id": str(completed["_id"]) if completed else None,
            "in_progress_assessment_id": str(active["_id"]) if active else None,
            "percentage": completed.get("percentage") if completed else None,
            "knowledge_level": completed.get("knowledge_level") if completed else None,
        })
    return out

@router.get("/{assessment_id}", response_model=AssessmentPublicResponse)
async def get_assessment(
    assessment_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    assessment = await AssessmentService.get_assessment_with_questions(assessment_id, user.id, db)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    now = datetime.now(timezone.utc)
    remaining_secs = 0
    if assessment.expires_at:
        expires_at = as_utc(assessment.expires_at)
        remaining_secs = max(0, int((expires_at - now).total_seconds()))

    public_questions = []
    for q in assessment.questions:
        opts = q.get("options", [])
        public_questions.append(AssessmentQuestionPublic(
            question_id=q.get("question_id"),
            topic=q.get("topic"),
            difficulty=q.get("difficulty"),
            question=q.get("question_text"),
            options=opts
        ))

    sub_doc = await db.subjects.find_one({"_id": oid(assessment.subject_id)}) if assessment.subject_id else None
    
    return AssessmentPublicResponse(
        assessment_id=assessment.id,
        subject_id=assessment.subject_id,
        subject_name=sub_doc["name"] if sub_doc else "Subject",
        title=assessment.title,
        duration_minutes=assessment.duration_minutes,
        total_questions=assessment.total_questions,
        status=assessment.status,
        started_at=assessment.started_at,
        expires_at=assessment.expires_at,
        remaining_seconds=remaining_secs,
        questions=public_questions
    )

@router.post("/{assessment_id}/submit", response_model=AssessmentResultResponse)
async def submit_assessment(
    assessment_id: str,
    payload: AssessmentSubmitRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    result_data, msg = await AssessmentService.submit_assessment(assessment_id, user, payload, db)
    if not result_data:
        raise HTTPException(status_code=400, detail=msg)
    # Regeneration deletes only future Scheduled entries, preserving completed work.
    if result_data.get("status") in {"completed", "expired"}:
        from app.services.planning_service import PlanningService
        await PlanningService.generate_plan_and_timetable(user, days_ahead=7, preserve_completed=True, db=db)
    return AssessmentResultResponse(**result_data)

@router.get("/{assessment_id}/result", response_model=AssessmentResultResponse)
async def get_assessment_result(
    assessment_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    assessment = await AssessmentService.get_assessment_with_questions(assessment_id, user.id, db)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    analysis = {}
    if assessment.analysis_json:
        try:
            analysis = json.loads(assessment.analysis_json)
        except Exception:
            pass

    correct_by_q = {}
    for q in assessment.questions:
        ans_doc = await db.assessment_answers.find_one({"assessment_id": assessment.id, "question_id": q["question_id"]})
        if ans_doc:
            correct_by_q[q["question_id"]] = ans_doc.get("is_correct", False)
            
    counts = {}
    for q in assessment.questions:
        c = counts.setdefault(q["topic"], {"total": 0, "correct": 0})
        c["total"] += 1
        c["correct"] += 1 if correct_by_q.get(q["question_id"]) else 0
        
    breakdown = []
    for topic, c in counts.items():
        pct = round(c["correct"] / max(1, c["total"]) * 100.0, 1)
        cat, prio = ("Strong", "Low") if pct >= 75 else (("Moderate", "Medium") if pct >= 50 else ("Needs Attention", "High"))
        question_subject_id = next(
            (q.get("subject_id") for q in assessment.questions if q.get("topic") == topic),
            assessment.subject_id,
        )
        performance = await db.topic_performance.find_one({
            "user_id": user.id,
            "subject_id": question_subject_id,
            "topic": topic,
        })
        blended = performance.get("score_percentage", pct) if performance else pct
        breakdown.append({
            "topic": topic,
            "total": c["total"],
            "correct": c["correct"],
            "percentage": blended if assessment.assessment_type == "retest" else pct,
            "category": performance.get("knowledge_category", cat) if performance else cat,
            "priority": prio,
            "previous_percentage": performance.get("previous_score_percentage") if performance and assessment.assessment_type == "retest" else None,
            "difference": round(blended - performance.get("previous_score_percentage", blended), 1) if performance and assessment.assessment_type == "retest" else None,
            "trend": performance.get("trend") if performance and assessment.assessment_type == "retest" else None,
        })

    sub_doc = await db.subjects.find_one({"_id": oid(assessment.subject_id)}) if assessment.subject_id else None
    
    return AssessmentResultResponse(
        assessment_id=assessment.id,
        subject_name=sub_doc["name"] if sub_doc else "Subject",
        status=assessment.status,
        score=assessment.score,
        total_questions=assessment.total_questions,
        percentage=assessment.percentage,
        knowledge_level=assessment.knowledge_level,
        anti_cheat_warnings=assessment.anti_cheat_warnings,
        topic_breakdown=breakdown,
        strengths=analysis.get("strengths", []),
        moderate_topics=analysis.get("moderate_topics", []),
        weak_topics=analysis.get("weak_topics", []),
        priority_topics=analysis.get("priority_topics", []),
        recommendations=analysis.get("recommendations", []),
        completed_at=assessment.completed_at,
        trend=assessment.retest_metadata.get("trend") if assessment.assessment_type == "retest" else None,
        feedback=analysis.get("feedback", []),
    )

@router.post("/{assessment_id}/anti-cheat-event")
async def log_anti_cheat_event(
    assessment_id: str,
    payload: AntiCheatEventRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    warnings = await AssessmentService.log_anti_cheat_event(
        assessment_id=assessment_id,
        user=user,
        event_type=payload.event_type,
        details=payload.details,
        db=db
    )
    return {"message": "Focus event logged.", "warning_count": warnings}
