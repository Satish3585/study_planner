from datetime import date, datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.utils.mongo import oid, doc_to_dict
from app.schemas.timetable import TimetableUpdateRequest, TimetableSkipRequest
from app.algorithms.personalized_drive import PersonalizedDriveAlgorithm


def _doc_to_entry(doc: dict) -> dict:
    if not doc:
        return {}
    d = doc_to_dict(doc)
    return d


class TimetableService:
    @staticmethod
    async def get_user_timetable(
        user_id: str, target_date: Optional[date], db: AsyncIOMotorDatabase
    ) -> List[dict]:
        query: dict = {"user_id": user_id}
        if target_date:
            query["date"] = target_date.isoformat()
        cursor = db.timetable_entries.find(query).sort([("date", 1), ("start_time", 1)])
        results = []
        async for doc in cursor:
            results.append(_doc_to_entry(doc))
        return results

    @staticmethod
    async def update_entry(
        entry_id: str, user_id: str, payload: TimetableUpdateRequest, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[dict], str]:
        updates: dict = {}
        if payload.date:
            updates["date"] = payload.date
        if payload.start_time:
            updates["start_time"] = payload.start_time
        if payload.end_time:
            updates["end_time"] = payload.end_time
        if payload.topic:
            updates["topic"] = payload.topic
        if payload.priority:
            updates["priority"] = payload.priority

        if not updates:
            return None, "No fields to update."
        try:
            doc = await db.timetable_entries.find_one_and_update(
                {"_id": oid(entry_id), "user_id": user_id},
                {"$set": updates},
                return_document=True,
            )
        except Exception:
            return None, "Timetable entry not found."
        if not doc:
            return None, "Timetable entry not found."
        return _doc_to_entry(doc), "Entry updated successfully."

    @staticmethod
    async def skip_entry(
        entry_id: str, user_id: str, payload: TimetableSkipRequest, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[dict], str]:
        try:
            doc = await db.timetable_entries.find_one_and_update(
                {"_id": oid(entry_id), "user_id": user_id},
                {"$set": {"status": "Skipped", "missed_reason": payload.reason}},
                return_document=True,
            )
        except Exception:
            return None, "Timetable entry not found."
        if not doc:
            return None, "Timetable entry not found."

        entry = _doc_to_entry(doc)
        entry_date = entry.get("date", "")

        future_cursor = db.timetable_entries.find({
            "user_id": user_id,
            "status": "Scheduled",
            "id": {"$ne": entry_id},
            "date": {"$gte": entry_date},
        }).sort([("date", 1), ("start_time", 1)])

        future_entries = []
        async for fe in future_cursor:
            future_entries.append(_doc_to_entry(fe))

        drive = PersonalizedDriveAlgorithm()
        missed_dict = {
            "subject_id": entry.get("subject_id"),
            "subject_name": entry.get("subject_name"),
            "topic": entry.get("topic"),
        }
        rebalanced = drive.rebalance_missed_session(missed_dict, payload.reason, future_entries)

        for r in rebalanced:
            try:
                await db.timetable_entries.update_one(
                    {"_id": oid(r["id"])},
                    {"$set": {"topic": r["topic"], "priority": r["priority"], "reason": r.get("reason")}},
                )
            except Exception:
                pass

        return entry, "Session skipped and workload rebalanced smoothly."

    @staticmethod
    async def complete_entry(
        entry_id: str, user_id: str, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[dict], str]:
        now = datetime.now(timezone.utc)
        try:
            doc = await db.timetable_entries.find_one_and_update(
                {"_id": oid(entry_id), "user_id": user_id},
                {"$set": {"status": "Completed", "actual_completed_at": now}},
                return_document=True,
            )
        except Exception:
            return None, "Timetable entry not found."
        if not doc:
            return None, "Timetable entry not found."
        return _doc_to_entry(doc), "Session marked as completed."
