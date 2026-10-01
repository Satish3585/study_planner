from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.checkpoint import (
    CheckpointPublicResponse, CheckpointQuestionPublic,
    CheckpointSubmitRequest, CheckpointResultResponse
)
from app.services.checkpoint_service import CheckpointService
from app.utils.mongo import oid

router = APIRouter(prefix="/checkpoints", tags=["Checkpoints"])

@router.post("/{session_id}/generate", status_code=status.HTTP_201_CREATED)
async def generate_checkpoint(
    session_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    checkpoint, msg = await CheckpointService.generate_checkpoint(session_id, user, db)
    if not checkpoint:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "checkpoint_id": checkpoint.id}

@router.get("/{checkpoint_id}", response_model=CheckpointPublicResponse)
async def get_checkpoint(
    checkpoint_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    cp = await CheckpointService.get_checkpoint_with_questions(checkpoint_id, user.id, db)
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint quiz not found.")

    public_q = []
    for q in cp.questions:
        opts = q.get("options", [])
        public_q.append(CheckpointQuestionPublic(
            question_id=q.get("question_id"),
            question=q.get("question_text"),
            options=opts
        ))

    sub_name = "Subject"
    if cp.subject_id:
        sub_doc = await db.subjects.find_one({"_id": oid(cp.subject_id)})
        if sub_doc:
            sub_name = sub_doc["name"]

    return CheckpointPublicResponse(
        checkpoint_id=cp.id,
        study_session_id=cp.study_session_id,
        subject_id=cp.subject_id,
        subject_name=sub_name,
        topic=cp.topic,
        total_questions=cp.total_questions,
        questions=public_q
    )

@router.post("/{checkpoint_id}/submit", response_model=CheckpointResultResponse)
async def submit_checkpoint(
    checkpoint_id: str,
    payload: CheckpointSubmitRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    result_data, msg = await CheckpointService.submit_checkpoint(checkpoint_id, user, payload, db)
    if not result_data:
        raise HTTPException(status_code=400, detail=msg)
    return CheckpointResultResponse(**result_data)
