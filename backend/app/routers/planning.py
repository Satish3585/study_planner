import json
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.services.planning_service import PlanningService

router = APIRouter(prefix="/planning", tags=["Planning"])

@router.post("/generate")
async def generate_plan(
    days_ahead: int = 7,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    result = await PlanningService.generate_plan_and_timetable(user, days_ahead=days_ahead, db=db)
    return {
        "message": "Personalized academic plan and schedule generated successfully.",
        **result
    }

@router.get("/current")
async def get_current_plan(
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    plan = await db.academic_plans.find_one({"user_id": user.id, "status": "active"})
    if not plan:
        raise HTTPException(status_code=404, detail="No active academic plan found. Please generate one.")

    topics = json.loads(plan.get("topics_plan_json", "[]"))
    ratios = json.loads(plan.get("allocation_ratio_json", "{}"))

    return {
        "id": str(plan["_id"]),
        "title": plan.get("title"),
        "total_allocated_hours": plan.get("total_allocated_hours", 0.0),
        "status": plan.get("status"),
        "allocation_ratio": ratios,
        "topics": topics,
        "generated_at": plan.get("generated_at")
    }
