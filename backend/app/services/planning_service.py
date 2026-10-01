import json
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import User
from app.models.academic_plan import AcademicPlan
from app.models.timetable import TimetableEntry
from app.utils.mongo import oid, doc_to_dict, model_to_doc
from app.algorithms.academic_planner import AcademicPlanner
from app.algorithms.personalized_drive import PersonalizedDriveAlgorithm


class PlanningService:
    @staticmethod
    async def generate_plan_and_timetable(
        user: User, days_ahead: int = 7, db: AsyncIOMotorDatabase = None,
        preserve_completed: bool = True,
    ) -> Dict[str, Any]:
        # 1. Subjects
        subjects_cursor = db.user_subjects.find({"user_id": user.id, "is_active": True})
        subjects_data = []
        async for us in subjects_cursor:
            subjects_data.append({"id": us["subject_id"], "name": us["subject_name"]})

        # 2. Topic performances
        tp_cursor = db.topic_performance.find({"user_id": user.id})
        topic_performances = []
        async for tp in tp_cursor:
            sub_doc = None
            try:
                sub_doc = await db.subjects.find_one({"_id": oid(tp["subject_id"])})
            except Exception:
                pass
            sub_name = sub_doc["name"] if sub_doc else "Unknown"
            cat = tp.get("knowledge_category", "Needs Attention")
            topic_performances.append({
                "subject_id": tp["subject_id"],
                "subject_name": sub_name,
                "topic": tp["topic"],
                "score_percentage": tp.get("score_percentage", 0.0),
                "category": cat,
                "priority": "High" if cat == "Needs Attention" else ("Medium" if cat == "Moderate" else "Low"),
                "trend": tp.get("trend"),
                "previous_score_percentage": tp.get("previous_score_percentage"),
            })

        # 3. Availability
        avail_doc = await db.availability.find_one({"user_id": user.id})
        if not avail_doc:
            avail_data = {
                "wake_time": "07:00", "sleep_time": "23:00",
                "college_start": "09:00", "college_end": "16:00",
                "morning_travel_minutes": 30, "evening_travel_minutes": 30,
                "meals": [
                    {"name": "Breakfast", "start": "08:00", "end": "08:30"},
                    {"name": "Lunch", "start": "13:00", "end": "13:45"},
                    {"name": "Dinner", "start": "20:00", "end": "20:45"},
                ],
                "exercise_time": "07:30", "exercise_minutes": 30,
                "commitments": [], "available_study_hours": 3.0,
                "preferred_study_time": "evening",
                "session_duration_minutes": 45, "break_duration_minutes": 10,
            }
        else:
            try:
                meals = json.loads(avail_doc.get("meal_times_json", "[]"))
            except Exception:
                meals = []
            try:
                commitments = json.loads(avail_doc.get("commitments_json", "[]"))
            except Exception:
                commitments = []
            avail_data = {
                "wake_time": avail_doc.get("wake_time", "07:00"),
                "sleep_time": avail_doc.get("sleep_time", "23:00"),
                "college_start": avail_doc.get("college_start", "09:00"),
                "college_end": avail_doc.get("college_end", "16:00"),
                "morning_travel_minutes": avail_doc.get("morning_travel_minutes", 30),
                "evening_travel_minutes": avail_doc.get("evening_travel_minutes", 30),
                "meals": meals, "commitments": commitments,
                "exercise_time": avail_doc.get("exercise_time", "07:30"),
                "exercise_minutes": avail_doc.get("exercise_minutes", 30),
                "available_study_hours": avail_doc.get("available_study_hours", 3.0),
                "preferred_study_time": avail_doc.get("preferred_study_time", "evening"),
                "session_duration_minutes": avail_doc.get("session_duration_minutes", 45),
                "break_duration_minutes": avail_doc.get("break_duration_minutes", 10),
            }

        # 4. Academic Plan
        planner = AcademicPlanner()
        total_weekly_hours = avail_data["available_study_hours"] * 7.0
        plan_dict = planner.build_academic_plan(subjects_data, topic_performances, total_weekly_hours)

        now = datetime.now(timezone.utc)
        active_plan_doc = await db.academic_plans.find_one({"user_id": user.id, "status": "active"})
        if not active_plan_doc:
            new_plan = {
                "user_id": user.id,
                "title": plan_dict["title"],
                "status": "active",
                "total_allocated_hours": plan_dict["total_allocated_hours"],
                "allocation_ratio_json": json.dumps(plan_dict["allocation_ratio"]),
                "topics_plan_json": json.dumps(plan_dict["topics"]),
                "generated_at": now, "updated_at": now,
            }
            res = await db.academic_plans.insert_one(new_plan)
            plan_id = str(res.inserted_id)
        else:
            plan_id = str(active_plan_doc["_id"])
            await db.academic_plans.update_one(
                {"_id": oid(plan_id)},
                {"$set": {
                    "total_allocated_hours": plan_dict["total_allocated_hours"],
                    "allocation_ratio_json": json.dumps(plan_dict["allocation_ratio"]),
                    "topics_plan_json": json.dumps(plan_dict["topics"]),
                    "updated_at": now,
                }},
            )

        # 5. Generate timetable
        drive = PersonalizedDriveAlgorithm()
        today = date.today()
        today_str = today.isoformat()

        if preserve_completed:
            await db.timetable_entries.delete_many({
                "user_id": user.id,
                "status": "Scheduled",
                "date": {"$gte": today_str},
            })
        else:
            await db.timetable_entries.delete_many({
                "user_id": user.id,
                "date": {"$gte": today_str},
                "status": {"$nin": ["Completed", "InProgress"]},
            })

        new_entries_raw = drive.generate_timetable(
            academic_plan_topics=plan_dict["topics"],
            availability_data=avail_data,
            start_date=today,
            days_count=days_ahead,
        )

        entries_to_insert = []
        for raw in new_entries_raw:
            entries_to_insert.append({
                "user_id": user.id,
                "academic_plan_id": plan_id,
                "date": raw["date"],
                "start_time": raw["start_time"],
                "end_time": raw["end_time"],
                "duration_minutes": raw["duration_minutes"],
                "subject_id": raw.get("subject_id"),
                "subject_name": raw["subject_name"],
                "topic": raw["topic"],
                "activity_type": raw["activity_type"],
                "priority": raw["priority"],
                "reason": raw.get("reason"),
                "status": "Scheduled",
                "created_at": now,
            })

        if entries_to_insert:
            await db.timetable_entries.insert_many(entries_to_insert)

        life_balance = drive.calculate_life_balance(avail_data)

        return {
            "plan_id": plan_id,
            "title": plan_dict["title"],
            "total_allocated_hours": plan_dict["total_allocated_hours"],
            "topics": plan_dict["topics"],
            "life_balance": life_balance,
            "entries_generated": len(entries_to_insert),
        }
