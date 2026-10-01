import json
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.availability import AvailabilitySchema, AvailabilityResponse
from app.algorithms.personalized_drive import PersonalizedDriveAlgorithm
from app.utils.mongo import oid

router = APIRouter(prefix="/availability", tags=["Availability"])

@router.get("", response_model=AvailabilityResponse)
async def get_availability(
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    avail = await db.availability.find_one({"user_id": user.id})
    drive = PersonalizedDriveAlgorithm()

    if not avail:
        default_meals = [
            {"name": "Breakfast", "start": "08:00", "end": "08:30"},
            {"name": "Lunch", "start": "13:00", "end": "13:45"},
            {"name": "Dinner", "start": "20:00", "end": "20:45"}
        ]
        default_dict = {
            "wake_time": "07:00", "sleep_time": "23:00",
            "college_start": "09:00", "college_end": "16:00",
            "morning_travel_minutes": 30, "evening_travel_minutes": 30,
            "available_study_hours": 3.0, "meals": default_meals,
            "exercise_time": "07:30", "exercise_minutes": 30,
            "commitments": [], "preferred_study_time": "evening",
            "session_duration_minutes": 45, "break_duration_minutes": 10
        }
        balance = drive.calculate_life_balance(default_dict)
        return AvailabilityResponse(
            id="0", user_id=user.id, balance_summary=balance, **default_dict
        )

    meals = json.loads(avail.get("meal_times_json", "[]"))
    commitments = json.loads(avail.get("commitments_json", "[]"))

    avail_dict = {
        "wake_time": avail.get("wake_time", "07:00"),
        "sleep_time": avail.get("sleep_time", "23:00"),
        "college_start": avail.get("college_start", "09:00"),
        "college_end": avail.get("college_end", "16:00"),
        "morning_travel_minutes": avail.get("morning_travel_minutes", 30),
        "evening_travel_minutes": avail.get("evening_travel_minutes", 30),
        "available_study_hours": avail.get("available_study_hours", 3.0),
        "meals": meals,
        "exercise_time": avail.get("exercise_time", "07:30"),
        "exercise_minutes": avail.get("exercise_minutes", 30),
        "commitments": commitments,
        "preferred_study_time": avail.get("preferred_study_time", "evening"),
        "session_duration_minutes": avail.get("session_duration_minutes", 45),
        "break_duration_minutes": avail.get("break_duration_minutes", 10)
    }
    balance = drive.calculate_life_balance(avail_dict)

    return AvailabilityResponse(
        id=str(avail["_id"]), user_id=user.id, balance_summary=balance, **avail_dict
    )

@router.put("", response_model=AvailabilityResponse)
async def update_availability(
    payload: AvailabilitySchema,
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    meals_json = json.dumps([m.model_dump() for m in payload.meals])
    commits_json = json.dumps([c.model_dump() for c in payload.commitments])

    update_data = {
        "day_of_week": payload.day_of_week or "all",
        "wake_time": payload.wake_time,
        "sleep_time": payload.sleep_time,
        "college_start": payload.college_start,
        "college_end": payload.college_end,
        "morning_travel_minutes": payload.morning_travel_minutes,
        "evening_travel_minutes": payload.evening_travel_minutes,
        "meal_times_json": meals_json,
        "exercise_time": payload.exercise_time,
        "exercise_minutes": payload.exercise_minutes,
        "commitments_json": commits_json,
        "available_study_hours": payload.available_study_hours,
        "preferred_study_time": payload.preferred_study_time,
        "session_duration_minutes": payload.session_duration_minutes,
        "break_duration_minutes": payload.break_duration_minutes
    }

    res = await db.availability.find_one_and_update(
        {"user_id": user.id},
        {"$set": update_data},
        upsert=True,
        return_document=True
    )

    drive = PersonalizedDriveAlgorithm()
    balance = drive.calculate_life_balance(payload.model_dump())

    return AvailabilityResponse(
        id=str(res["_id"]),
        user_id=user.id,
        balance_summary=balance,
        **payload.model_dump()
    )
