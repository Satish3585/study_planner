from typing import List
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.notifications import NotificationResponse, AIRecommendationResponse
from app.utils.mongo import oid

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    cursor = db.notifications.find({"user_id": user.id}).sort("created_at", -1).limit(50)
    results = []
    async for n in cursor:
        results.append(NotificationResponse(
            id=str(n["_id"]),
            title=n["title"],
            message=n["message"],
            type=n.get("type", "info"),
            is_read=n.get("is_read", False),
            created_at=n["created_at"]
        ))
    return results

@router.post("/{notif_id}/read")
async def mark_notification_read(
    notif_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    await db.notifications.update_one(
        {"_id": oid(notif_id), "user_id": user.id},
        {"$set": {"is_read": True}}
    )
    return {"message": "Notification marked as read."}

@router.get("/recommendations", response_model=List[AIRecommendationResponse])
async def get_recommendations(
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    cursor = db.ai_recommendations.find(
        {"user_id": user.id, "is_dismissed": False}
    ).sort("created_at", -1).limit(10)
    
    results = []
    async for r in cursor:
        results.append(AIRecommendationResponse(
            id=str(r["_id"]),
            recommendation_text=r["recommendation_text"],
            category=r.get("category", "Topic Focus"),
            topic=r.get("topic"),
            priority=r.get("priority", "Medium"),
            is_dismissed=False,
            created_at=r["created_at"]
        ))
    return results

@router.post("/recommendations/{rec_id}/dismiss")
async def dismiss_recommendation(
    rec_id: str,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    await db.ai_recommendations.update_one(
        {"_id": oid(rec_id), "user_id": user.id},
        {"$set": {"is_dismissed": True}}
    )
    return {"message": "Recommendation dismissed."}
