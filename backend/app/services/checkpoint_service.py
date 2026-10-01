import json
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import User
from app.models.checkpoint import Checkpoint, CheckpointAnswer
from app.schemas.checkpoint import CheckpointSubmitRequest
from app.utils.mongo import oid, doc_to_dict, model_to_doc
from app.ai import get_ai_provider


def _doc_to_checkpoint(doc: dict) -> Optional[Checkpoint]:
    if not doc:
        return None
    d = doc_to_dict(doc)
    return Checkpoint(
        id=d.get("id"),
        user_id=d["user_id"],
        subject_id=d["subject_id"],
        topic=d["topic"],
        study_session_id=d.get("study_session_id"),
        total_questions=d.get("total_questions", 3),
        score=d.get("score", 0),
        percentage=d.get("percentage", 0.0),
        questions=d.get("questions", []),
        status=d.get("status", "generated"),
        completed_at=d.get("completed_at"),
        created_at=d.get("created_at", datetime.now(timezone.utc)),
    )


class CheckpointService:
    @staticmethod
    async def generate_checkpoint(
        session_id: str, user: User, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[Checkpoint], str]:
        try:
            session_doc = await db.study_sessions.find_one(
                {"_id": oid(session_id), "user_id": user.id}
            )
        except Exception:
            return None, "Study session not found."

        if not session_doc:
            return None, "Study session not found."

        subject_id = session_doc.get("subject_id", "")
        topic = session_doc.get("topic", "General Studies")
        subject_name = "General Studies"

        if subject_id:
            try:
                sub_doc = await db.subjects.find_one({"_id": oid(subject_id)})
                if sub_doc:
                    subject_name = sub_doc["name"]
            except Exception:
                pass

        ai = get_ai_provider()
        questions_raw = await ai.generate_checkpoint_questions(
            subject=subject_name, topic=topic, count=3, level="intermediate"
        )

        questions_embedded = [
            {
                "question_id": q.get("question_id", f"cp_{idx+1}"),
                "question_text": q.get("question", ""),
                "options": q.get("options", []),
                "correct_answer": q.get("correct_answer", ""),
                "explanation": q.get("explanation", ""),
            }
            for idx, q in enumerate(questions_raw)
        ]

        checkpoint = Checkpoint(
            user_id=user.id,
            study_session_id=session_id,
            subject_id=subject_id or user.id,
            topic=topic,
            total_questions=len(questions_embedded),
            questions=questions_embedded,
            status="generated",
        )
        result = await db.checkpoints.insert_one(model_to_doc(checkpoint))
        checkpoint.id = str(result.inserted_id)
        return checkpoint, "Checkpoint quiz generated."

    @staticmethod
    async def get_checkpoint_with_questions(
        checkpoint_id: str, user_id: str, db: AsyncIOMotorDatabase
    ) -> Optional[Checkpoint]:
        try:
            doc = await db.checkpoints.find_one(
                {"_id": oid(checkpoint_id), "user_id": user_id}
            )
        except Exception:
            return None
        return _doc_to_checkpoint(doc)

    @staticmethod
    async def submit_checkpoint(
        checkpoint_id: str, user: User, payload: CheckpointSubmitRequest, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        checkpoint = await CheckpointService.get_checkpoint_with_questions(checkpoint_id, user.id, db)
        if not checkpoint:
            return None, "Checkpoint not found."
        if checkpoint.status == "completed":
            return None, "Checkpoint has already been submitted."

        questions_by_qid = {q["question_id"]: q for q in checkpoint.questions}
        answers_dict = {a.question_id: a.selected_answer for a in payload.answers}

        total_correct = 0
        reviews = []
        now = datetime.now(timezone.utc)

        for qid, q in questions_by_qid.items():
            opts = q.get("options", [])
            student_ans = answers_dict.get(qid, "Unanswered")
            is_correct = False
            if student_ans.strip().lower() == q["correct_answer"].strip().lower():
                is_correct = True
            elif student_ans.strip().lower() in ["a", "b", "c", "d"]:
                idx = ord(student_ans.strip().lower()) - ord("a")
                if 0 <= idx < len(opts) and opts[idx].strip().lower() == q["correct_answer"].strip().lower():
                    is_correct = True

            if is_correct:
                total_correct += 1

            reviews.append({
                "question_id": qid,
                "question": q["question_text"],
                "options": opts,
                "selected_answer": student_ans,
                "correct_answer": q["correct_answer"],
                "is_correct": is_correct,
                "explanation": q.get("explanation", ""),
            })

        total_q = len(checkpoint.questions)
        pct = round((total_correct / max(1, total_q)) * 100.0, 1)

        await db.checkpoints.update_one(
            {"_id": oid(checkpoint.id)},
            {"$set": {"score": total_correct, "percentage": pct, "status": "completed", "completed_at": now}},
        )

        # Adaptive learning: update TopicPerformance
        tp_doc = await db.topic_performance.find_one(
            {"user_id": user.id, "subject_id": checkpoint.subject_id, "topic": checkpoint.topic}
        )
        old_score = tp_doc["score_percentage"] if tp_doc else 50.0
        new_score = round((0.40 * old_score) + (0.60 * pct), 1)

        if new_score >= 75.0:
            new_cat, new_prio = "Strong", 0.5
        elif new_score >= 50.0:
            new_cat, new_prio = "Moderate", 1.0
        else:
            new_cat, new_prio = "Needs Attention", 1.5

        await db.topic_performance.update_one(
            {"user_id": user.id, "subject_id": checkpoint.subject_id, "topic": checkpoint.topic},
            {"$set": {
                "score_percentage": new_score,
                "knowledge_category": new_cat,
                "priority_weight": new_prio,
                "updated_at": now,
            }, "$setOnInsert": {
                "user_id": user.id,
                "subject_id": checkpoint.subject_id,
                "topic": checkpoint.topic,
                "total_questions": total_q,
                "correct_questions": total_correct,
            }},
            upsert=True,
        )

        # Grounded adaptive recommendation
        sub_doc = await db.subjects.find_one({"_id": oid(checkpoint.subject_id)}) if checkpoint.subject_id else None
        sub_name = sub_doc["name"] if sub_doc else "Subject"

        if new_score > old_score:
            rec_text = f"Your mastery of '{checkpoint.topic}' improved from {old_score}% to {new_score}%. The planning engine will automatically transition upcoming sessions into applied problem solving."
        else:
            rec_text = f"Checkpoint showed areas for review in '{checkpoint.topic}' (score: {new_score}%). Flagged for a 15-minute quick revision in your next schedule."

        await db.ai_recommendations.insert_one({
            "user_id": user.id,
            "category": "Adaptive Learning",
            "recommendation_text": rec_text,
            "topic": checkpoint.topic,
            "priority": "High" if new_cat == "Needs Attention" else "Medium",
            "is_dismissed": False,
            "created_at": now,
        })

        return {
            "checkpoint_id": checkpoint.id,
            "subject_name": sub_name,
            "topic": checkpoint.topic,
            "score": total_correct,
            "total_questions": total_q,
            "percentage": pct,
            "status": "completed",
            "reviews": reviews,
            "topic_level_updated": f"Score updated to {new_score}% ({new_cat})",
            "adaptive_recommendation": rec_text,
            "completed_at": now,
        }, "Checkpoint submitted and knowledge profile dynamically updated."
