from datetime import datetime, timezone
from typing import Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import User
from app.models.study_session import StudySession
from app.schemas.study import StudySessionStartRequest
from app.utils.mongo import oid, doc_to_dict, model_to_doc


def _doc_to_session(doc: dict) -> Optional[StudySession]:
    if not doc:
        return None
    d = doc_to_dict(doc)
    return StudySession(
        id=d.get("id"),
        user_id=d["user_id"],
        topic=d["topic"],
        timetable_entry_id=d.get("timetable_entry_id"),
        subject_id=d.get("subject_id"),
        objective=d.get("objective"),
        scheduled_duration_minutes=d.get("scheduled_duration_minutes", 45),
        actual_duration_minutes=d.get("actual_duration_minutes", 0.0),
        status=d.get("status", "started"),
        started_at=d.get("started_at", datetime.now(timezone.utc)),
        active_started_at=d.get("active_started_at", d.get("started_at")),
        paused_at=d.get("paused_at"),
        ended_at=d.get("ended_at"),
        focus_score=d.get("focus_score", 100.0),
        interruption_count=d.get("interruption_count", 0),
        completion_percentage=d.get("completion_percentage", 0.0),
        partial_completion=d.get("partial_completion", False),
    )


class StudyService:
    @staticmethod
    async def start_session(
        user: User, req: StudySessionStartRequest, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[StudySession], str]:
        now = datetime.now(timezone.utc)
        sub_id = str(req.subject_id) if req.subject_id else None
        topic = req.topic or "Focused Study"
        objective = req.objective or f"Master key concepts in {topic}"
        duration = req.duration_minutes or 45
        tt_entry_id = str(req.timetable_entry_id) if req.timetable_entry_id else None

        if tt_entry_id:
            try:
                tt_doc = await db.timetable_entries.find_one(
                    {"_id": oid(tt_entry_id), "user_id": user.id}
                )
                if tt_doc and tt_doc.get("activity_type") != "Break" and tt_doc.get("status") in {"Scheduled", "InProgress"}:
                    sub_id = tt_doc.get("subject_id")
                    topic = tt_doc["topic"]
                    duration = tt_doc["duration_minutes"]
                    objective = f"Complete scheduled {tt_doc.get('activity_type', 'Study')} block on {topic}"
                    await db.timetable_entries.update_one(
                        {"_id": oid(tt_entry_id)},
                        {"$set": {"status": "InProgress", "actual_started_at": now}},
                    )
                else:
                    return None, "Timetable entry is not available for a study session."
            except Exception:
                return None, "Timetable entry not found."

        if tt_entry_id and await db.study_sessions.find_one({
            "user_id": user.id, "timetable_entry_id": tt_entry_id,
            "status": {"$in": ["started", "resumed", "paused"]},
        }):
            return None, "A session for this timetable entry is already active."

        session = StudySession(
            user_id=user.id,
            timetable_entry_id=tt_entry_id,
            subject_id=sub_id,
            topic=topic,
            objective=objective,
            scheduled_duration_minutes=duration,
            actual_duration_minutes=0.0,
            status="started",
            started_at=now,
            active_started_at=now,
            focus_score=100.0,
            interruption_count=0,
        )
        result = await db.study_sessions.insert_one(model_to_doc(session))
        session.id = str(result.inserted_id)
        return session, "Study session started."

    @staticmethod
    async def pause_session(
        session_id: str, user_id: str, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[StudySession], str]:
        now = datetime.now(timezone.utc)
        current = await db.study_sessions.find_one({"_id": oid(session_id), "user_id": user_id})
        if not current:
            return None, "Session not found."
        active_started = current.get("active_started_at") or current.get("started_at")
        elapsed = float(current.get("actual_duration_minutes", 0.0))
        if active_started:
            elapsed += max(0.0, (now - active_started).total_seconds() / 60.0)
        doc = await db.study_sessions.find_one_and_update(
            {"_id": oid(session_id), "user_id": user_id},
            {"$set": {"status": "paused", "paused_at": now, "active_started_at": None,
                      "actual_duration_minutes": round(elapsed, 1)}},
            return_document=True,
        )
        if not doc:
            return None, "Session not found."
        return _doc_to_session(doc), "Study session paused."

    @staticmethod
    async def resume_session(
        session_id: str, user_id: str, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[StudySession], str]:
        doc = await db.study_sessions.find_one_and_update(
            {"_id": oid(session_id), "user_id": user_id},
            {"$set": {"status": "resumed", "paused_at": None, "active_started_at": datetime.now(timezone.utc)}},
            return_document=True,
        )
        if not doc:
            return None, "Session not found."
        return _doc_to_session(doc), "Study session resumed."

    @staticmethod
    async def finish_session(
        session_id: str, user_id: str, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[StudySession], str]:
        now = datetime.now(timezone.utc)
        orig_doc = await db.study_sessions.find_one(
            {"_id": oid(session_id), "user_id": user_id}
        )
        if not orig_doc:
            return None, "Session not found."
        if orig_doc.get("status") == "completed":
            return _doc_to_session(orig_doc), "Study session already completed."

        active_started_at = orig_doc.get("active_started_at") or orig_doc.get("started_at")
        actual_mins = float(orig_doc.get("actual_duration_minutes", 0.0))
        if active_started_at:
            actual_mins += max(0.0, (now - active_started_at).total_seconds() / 60.0)
        actual_mins = round(max(1.0, actual_mins), 1)
        scheduled = float(orig_doc.get("scheduled_duration_minutes") or 1)
        completion = round(min(100.0, actual_mins / scheduled * 100.0), 1)

        doc = await db.study_sessions.find_one_and_update(
            {"_id": oid(session_id), "user_id": user_id},
            {"$set": {"status": "completed", "ended_at": now, "actual_duration_minutes": actual_mins,
                      "completion_percentage": completion, "partial_completion": completion < 100.0,
                      "active_started_at": None}},
            return_document=True,
        )

        # Update linked timetable entry
        tt_entry_id = orig_doc.get("timetable_entry_id")
        if tt_entry_id:
            try:
                await db.timetable_entries.update_one(
                    {"_id": oid(tt_entry_id)},
                    {"$set": {"status": "Completed", "actual_completed_at": now}},
                )
            except Exception:
                pass

        return _doc_to_session(doc), "Study session completed."

    @staticmethod
    async def log_focus_event(
        session_id: str, user_id: str, event_type: str, details: Optional[str], db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[StudySession], int]:
        now = datetime.now(timezone.utc)
        doc = await db.study_sessions.find_one(
            {"_id": oid(session_id), "user_id": user_id}
        )
        if not doc:
            return None, 0

        new_count = doc.get("interruption_count", 0) + 1
        new_focus = max(50.0, 100.0 - (new_count * 3.0))

        updated = await db.study_sessions.find_one_and_update(
            {"_id": oid(session_id)},
            {"$set": {"interruption_count": new_count, "focus_score": new_focus}},
            return_document=True,
        )
        await db.focus_events.insert_one({
            "study_session_id": session_id,
            "user_id": user_id,
            "event_type": event_type,
            "details": details,
            "timestamp": now,
        })
        return _doc_to_session(updated), new_count
