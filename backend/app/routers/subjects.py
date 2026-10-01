from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.subjects import SubjectCreate, SubjectResponse, ConfirmSubjectsRequest
from app.utils.mongo import oid
from datetime import datetime, timezone

router = APIRouter(prefix="/subjects", tags=["Subjects"])

@router.get("", response_model=List[SubjectResponse])
async def get_user_subjects(
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    results = []
    cursor = db.user_subjects.find({"user_id": user.id})
    async for us in cursor:
        sub_doc = await db.subjects.find_one({"_id": oid(us["subject_id"])})
        if sub_doc:
            results.append(SubjectResponse(
                id=str(sub_doc["_id"]),
                name=sub_doc["name"],
                code=sub_doc.get("code"),
                description=sub_doc.get("description"),
                is_active=us.get("is_active", True),
                confidence_level=us.get("confidence_level", "Moderate")
            ))
    return results

@router.post("", response_model=SubjectResponse)
async def add_subject(
    payload: SubjectCreate,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    name_clean = payload.name.strip()
    sub_doc = await db.subjects.find_one({"name": {"$regex": f"^{name_clean}$", "$options": "i"}})
    
    now = datetime.now(timezone.utc)
    if not sub_doc:
        res = await db.subjects.insert_one({
            "name": name_clean,
            "code": payload.code,
            "description": payload.description,
            "created_at": now
        })
        sub_id = str(res.inserted_id)
    else:
        sub_id = str(sub_doc["_id"])

    await db.user_subjects.update_one(
        {"user_id": user.id, "subject_id": sub_id},
        {"$set": {"is_active": True, "subject_name": name_clean},
         "$setOnInsert": {"confidence_level": "Moderate", "created_at": now}},
        upsert=True
    )

    return SubjectResponse(
        id=sub_id,
        name=name_clean,
        code=payload.code,
        description=payload.description,
        is_active=True,
        confidence_level="Moderate"
    )

@router.post("/confirm")
async def confirm_subjects(
    payload: ConfirmSubjectsRequest,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    if not payload.subjects:
        raise HTTPException(status_code=400, detail="Please select or provide at least one subject.")

    await db.user_subjects.update_many(
        {"user_id": user.id},
        {"$set": {"is_active": False}}
    )

    now = datetime.now(timezone.utc)
    for sub_name in payload.subjects:
        clean = sub_name.strip()
        if not clean:
            continue
        sub_doc = await db.subjects.find_one({"name": {"$regex": f"^{clean}$", "$options": "i"}})
        if not sub_doc:
            res = await db.subjects.insert_one({"name": clean, "created_at": now})
            sub_id = str(res.inserted_id)
        else:
            sub_id = str(sub_doc["_id"])

        await db.user_subjects.update_one(
            {"user_id": user.id, "subject_id": sub_id},
            {"$set": {"is_active": True, "subject_name": clean},
             "$setOnInsert": {"confidence_level": "Moderate", "created_at": now}},
            upsert=True
        )

    return {"message": "Subjects successfully confirmed.", "confirmed_count": len(payload.subjects)}

@router.delete("/{subject_id}")
async def remove_subject(
    subject_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    res = await db.user_subjects.update_one(
        {"user_id": user.id, "subject_id": subject_id},
        {"$set": {"is_active": False}}
    )
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="Subject not found in student's profile.")
    
    return {"message": "Subject removed from active list."}
