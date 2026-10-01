import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import User
from app.models.assessment import Assessment, TopicPerformance
from app.schemas.assessment import AssessmentStartRequest, AssessmentSubmitRequest, RetestStartRequest
from app.utils.mongo import as_utc, oid, doc_to_dict, model_to_doc
from app.ai import get_ai_provider


def _build_assessment(doc: dict) -> Optional[Assessment]:
    if not doc:
        return None
    d = doc_to_dict(doc)
    return Assessment(
        id=d.get("id"),
        user_id=d["user_id"],
        subject_id=d["subject_id"],
        title=d["title"],
        assessment_type=d.get("assessment_type", "baseline"),
        source_assessment_id=d.get("source_assessment_id"),
        retest_topics=d.get("retest_topics", []),
        retest_metadata=d.get("retest_metadata", {}),
        retest_date=d.get("retest_date"),
        retest_kind=d.get("retest_kind"),
        duration_minutes=d.get("duration_minutes", 30),
        total_questions=d.get("total_questions", 0),
        status=d.get("status", "not_started"),
        started_at=d.get("started_at"),
        expires_at=d.get("expires_at"),
        completed_at=d.get("completed_at"),
        score=d.get("score", 0),
        percentage=d.get("percentage", 0.0),
        knowledge_level=d.get("knowledge_level", "Needs Assessment"),
        anti_cheat_warnings=d.get("anti_cheat_warnings", 0),
        questions=d.get("questions", []),
        analysis_json=d.get("analysis_json"),
        created_at=d.get("created_at", datetime.now(timezone.utc)),
    )


class AssessmentService:
    @staticmethod
    def select_completed_topic_pairs(entries: List[dict]) -> List[dict]:
        """Return distinct completed study subject/topic pairs in stable order."""
        pairs: List[dict] = []
        seen: set[tuple[str, str]] = set()
        for entry in entries:
            if entry.get("status") != "Completed" or entry.get("activity_type") == "Break":
                continue
            subject_id = entry.get("subject_id")
            topic = entry.get("topic")
            if not subject_id or not topic:
                continue
            key = (str(subject_id), str(topic))
            if key not in seen:
                seen.add(key)
                pairs.append({"subject_id": key[0], "topic": key[1]})
        return pairs

    @staticmethod
    def blend_topic_score(retest_score: float, previous_score: float) -> float:
        return round((0.6 * retest_score) + (0.4 * previous_score), 1)

    @staticmethod
    async def _retest_topics(user_id: str, subject_id: str, db: AsyncIOMotorDatabase) -> List[str]:
        """Prefer completed study topics, then weak historical topics."""
        cursor = db.timetable_entries.find({
            "user_id": user_id, "subject_id": subject_id, "status": "Completed",
            "activity_type": {"$ne": "Break"},
        }).sort("actual_completed_at", -1).limit(20)
        topics = []
        async for entry in cursor:
            topic = entry.get("topic")
            if topic and topic not in topics:
                topics.append(topic)
        if topics:
            return topics[:6]
        weak = db.topic_performance.find({
            "user_id": user_id, "subject_id": subject_id,
            "knowledge_category": {"$in": ["Needs Attention", "Moderate"]},
        }).sort("score_percentage", 1).limit(6)
        async for item in weak:
            if item.get("topic") and item["topic"] not in topics:
                topics.append(item["topic"])
        return topics or ["Core concepts"]

    @staticmethod
    async def start_assessment(
        user: User, req: AssessmentStartRequest, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[Assessment], str]:
        subject_doc = await db.subjects.find_one({"_id": oid(str(req.subject_id))})
        if not subject_doc:
            return None, "Subject not found."

        subject_name = subject_doc["name"]
        subject_id = str(subject_doc["_id"])

        ai = get_ai_provider()
        questions_raw = await ai.generate_assessment_questions(
            subject=subject_name,
            course=user.course,
            semester=user.semester,
            count=req.question_count,
            difficulty="adaptive",
        )

        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=req.duration_minutes)

        # Embed questions directly in assessment document
        questions_embedded = [
            {
                "question_id": q.get("question_id", f"q{idx+1}"),
                "topic": q.get("topic", "General"),
                "difficulty": q.get("difficulty", "medium"),
                "question_text": q.get("question", ""),
                "options": q.get("options", []),
                "correct_answer": q.get("correct_answer", ""),
                "explanation": q.get("explanation", ""),
                "order_idx": idx,
            }
            for idx, q in enumerate(questions_raw)
        ]

        assessment = Assessment(
            user_id=user.id,
            subject_id=subject_id,
            title=f"{subject_name} Baseline Assessment",
            assessment_type="baseline",
            duration_minutes=req.duration_minutes,
            total_questions=len(questions_embedded),
            status="in_progress",
            started_at=now,
            expires_at=expires,
            questions=questions_embedded,
        )

        result = await db.assessments.insert_one(model_to_doc(assessment))
        assessment.id = str(result.inserted_id)
        return assessment, "Assessment started successfully."

    @staticmethod
    async def start_retest(
        user: User, req: RetestStartRequest, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[Assessment], str]:
        subject_doc = await db.subjects.find_one({"_id": oid(str(req.subject_id))})
        if not subject_doc:
            return None, "Subject not found."
        subject_id = str(subject_doc["_id"])
        active = await db.assessments.find_one({
            "user_id": user.id, "subject_id": subject_id, "assessment_type": "retest",
            "status": "in_progress",
        })
        if active:
            return _build_assessment(active), "A retest is already in progress."
        topics = [req.topic] if req.topic else await AssessmentService._retest_topics(user.id, subject_id, db)
        ai = get_ai_provider()
        questions_raw = []
        for topic in topics:
            generated = await ai.generate_assessment_questions(
                subject=f"{subject_doc['name']} — {topic}",
                course=user.course, semester=user.semester,
                count=min(3, req.question_count), difficulty="adaptive",
            )
            for question in generated[:3]:
                question["topic"] = topic
                questions_raw.append(question)
            if len(questions_raw) >= 20:
                break
        now = datetime.now(timezone.utc)
        embedded = [{
            "question_id": q.get("question_id", f"q{i + 1}"),
            "topic": q.get("topic") or topics[i % len(topics)],
            "difficulty": q.get("difficulty", "medium"),
            "question_text": q.get("question", ""),
            "options": q.get("options", []),
            "correct_answer": q.get("correct_answer", ""),
            "explanation": q.get("explanation", ""),
            "order_idx": i,
        } for i, q in enumerate(questions_raw[:20])]
        assessment = Assessment(
            user_id=user.id, subject_id=subject_id,
            title=f"{subject_doc['name']} Retest", assessment_type="retest",
            source_assessment_id=req.source_assessment_id,
            retest_topics=topics, retest_metadata={"state": "in_progress"},
            duration_minutes=req.duration_minutes, total_questions=len(embedded),
            status="in_progress", started_at=now,
            expires_at=now + timedelta(minutes=req.duration_minutes), questions=embedded,
        )
        result = await db.assessments.insert_one(model_to_doc(assessment))
        assessment.id = str(result.inserted_id)
        return assessment, "Retest started successfully."

    @staticmethod
    async def start_daily_retest(
        user: User, retest_date: str, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[Assessment], str]:
        existing = await db.assessments.find_one({
            "user_id": user.id,
            "assessment_type": "retest",
            "retest_date": retest_date,
            "retest_kind": "daily",
            "status": {"$in": ["in_progress", "completed"]},
        })
        if existing:
            return _build_assessment(existing), "A retest already exists for this date."

        entries = await db.timetable_entries.find({
            "user_id": user.id,
            "date": retest_date,
        }).sort([("start_time", 1), ("_id", 1)]).to_list(None)
        pairs = AssessmentService.select_completed_topic_pairs(entries)
        if not pairs:
            return None, "No completed study topics were found for that date."

        subject_ids = list(dict.fromkeys(pair["subject_id"] for pair in pairs))
        subject_docs = {}
        for subject_id in subject_ids:
            try:
                doc = await db.subjects.find_one({"_id": oid(subject_id)})
            except Exception:
                doc = None
            if doc:
                subject_docs[subject_id] = doc

        ai = get_ai_provider()
        questions_raw: List[dict] = []
        for pair in pairs:
            subject_doc = subject_docs.get(pair["subject_id"])
            subject_name = subject_doc.get("name", "Subject") if subject_doc else "Subject"
            prior = await db.topic_performance.find_one({
                "user_id": user.id,
                "subject_id": pair["subject_id"],
                "topic": pair["topic"],
            })
            previous_score = float(prior.get("score_percentage", 0.0)) if prior else 0.0
            difficulty = "hard" if previous_score >= 75 else ("medium" if previous_score >= 50 else "easy")
            generated = await ai.generate_assessment_questions(
                subject=f"{subject_name} — {pair['topic']}",
                course=user.course,
                semester=user.semester,
                count=3,
                difficulty=difficulty,
            )
            for question in generated[:3]:
                question["topic"] = pair["topic"]
                question["subject_id"] = pair["subject_id"]
                questions_raw.append(question)
                if len(questions_raw) >= 20:
                    break
            if len(questions_raw) >= 20:
                break

        now = datetime.now(timezone.utc)
        embedded = [{
            "question_id": f"q{i + 1}",
            "topic": question.get("topic", "General"),
            "subject_id": question.get("subject_id", subject_ids[0]),
            "difficulty": question.get("difficulty", "medium"),
            "question_text": question.get("question", ""),
            "options": question.get("options", []),
            "correct_answer": question.get("correct_answer", ""),
            "explanation": question.get("explanation", ""),
            "order_idx": i,
        } for i, question in enumerate(questions_raw[:20])]
        first_subject = subject_docs.get(subject_ids[0], {})
        assessment = Assessment(
            user_id=user.id,
            subject_id=subject_ids[0],
            title=f"Daily Retest · {retest_date}",
            assessment_type="retest",
            retest_date=retest_date,
            retest_kind="daily",
            retest_topics=[f"{pair['subject_id']}::{pair['topic']}" for pair in pairs],
            retest_metadata={"state": "in_progress", "subject_ids": subject_ids},
            duration_minutes=max(1, len(embedded) * 2),
            total_questions=len(embedded),
            status="in_progress",
            started_at=now,
            expires_at=now + timedelta(minutes=max(1, len(embedded) * 2)),
            questions=embedded,
        )
        try:
            result = await db.assessments.insert_one(model_to_doc(assessment))
        except Exception:
            existing = await db.assessments.find_one({
                "user_id": user.id,
                "assessment_type": "retest",
                "retest_date": retest_date,
                "retest_kind": "daily",
            })
            if existing:
                return _build_assessment(existing), "A retest already exists for this date."
            raise
        assessment.id = str(result.inserted_id)
        return assessment, "Daily retest started successfully."

    @staticmethod
    async def weekly_retest_state(user: User, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
        latest = await db.assessments.find_one(
            {"user_id": user.id, "assessment_type": "retest", "retest_kind": "weekly"},
            sort=[("completed_at", -1)],
        )
        now = datetime.now(timezone.utc)
        if latest and as_utc(latest.get("completed_at")) and now - as_utc(latest["completed_at"]) < timedelta(days=7):
            return {"state": "not_due", "assessment_id": str(latest["_id"]), "available_at": as_utc(latest["completed_at"]) + timedelta(days=7)}
        topics = await db.topic_performance.find({"user_id": user.id}).sort("score_percentage", 1).limit(20).to_list(None)
        return {"state": "available" if topics else "unavailable", "topic_count": len(topics)}

    @staticmethod
    async def start_weekly_retest(user: User, db: AsyncIOMotorDatabase) -> Tuple[Optional[Assessment], str]:
        state = await AssessmentService.weekly_retest_state(user, db)
        if state["state"] != "available":
            return None, "Weekly retest is not currently due or there are no assessed topics."
        topics = await db.topic_performance.find({"user_id": user.id}).sort("score_percentage", 1).limit(20).to_list(None)
        subject_ids = list(dict.fromkeys(str(t["subject_id"]) for t in topics if t.get("subject_id")))
        subject_docs = {}
        for sid in subject_ids:
            try:
                doc = await db.subjects.find_one({"_id": oid(sid)})
            except Exception:
                doc = None
            if doc:
                subject_docs[sid] = doc
        ai = get_ai_provider()
        questions_raw: List[dict] = []
        selected_topics: List[str] = []
        for performance in topics:
            sid = str(performance["subject_id"])
            topic = performance.get("topic")
            if not topic:
                continue
            selected_topics.append(f"{sid}::{topic}")
            subject_name = subject_docs.get(sid, {}).get("name", "Subject")
            score = float(performance.get("score_percentage", 0))
            difficulty = "easy" if score < 50 else ("medium" if score < 75 else "hard")
            generated = await ai.generate_assessment_questions(
                subject=f"{subject_name} — {topic}", course=user.course, semester=user.semester,
                count=3, difficulty=difficulty,
            )
            for question in generated[:3]:
                question["topic"] = topic
                question["subject_id"] = sid
                questions_raw.append(question)
                if len(questions_raw) >= 20:
                    break
            if len(questions_raw) >= 20:
                break
        now = datetime.now(timezone.utc)
        embedded = [{
            "question_id": f"q{i + 1}", "topic": q.get("topic", "General"),
            "subject_id": q.get("subject_id", subject_ids[0] if subject_ids else ""),
            "difficulty": q.get("difficulty", "medium"), "question_text": q.get("question", ""),
            "options": q.get("options", []), "correct_answer": q.get("correct_answer", ""),
            "explanation": q.get("explanation", ""), "order_idx": i,
        } for i, q in enumerate(questions_raw[:20])]
        assessment = Assessment(
            user_id=user.id, subject_id=subject_ids[0] if subject_ids else "",
            title="Weekly Retest", assessment_type="retest", retest_kind="weekly",
            retest_date=now.date().isoformat(), retest_topics=selected_topics,
            retest_metadata={"state": "in_progress", "subject_ids": subject_ids},
            duration_minutes=max(1, len(embedded) * 2), total_questions=len(embedded),
            status="in_progress", started_at=now,
            expires_at=now + timedelta(minutes=max(1, len(embedded) * 2)), questions=embedded,
        )
        result = await db.assessments.insert_one(model_to_doc(assessment))
        assessment.id = str(result.inserted_id)
        return assessment, "Weekly retest started successfully."

    @staticmethod
    async def retest_state(user: User, subject_id: str, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
        active = await db.assessments.find_one({
            "user_id": user.id, "subject_id": subject_id, "assessment_type": "retest",
            "status": "in_progress",
        })
        if active:
            return {"subject_id": subject_id, "state": "in_progress", "topics": active.get("retest_topics", []),
                    "assessment_id": str(active["_id"])}
        latest = await db.assessments.find_one(
            {"user_id": user.id, "subject_id": subject_id, "assessment_type": "retest"},
            sort=[("completed_at", -1)],
        )
        if latest:
            return {"subject_id": subject_id, "state": latest.get("retest_metadata", {}).get("state", latest.get("status", "completed")),
                    "topics": latest.get("retest_topics", []), "assessment_id": str(latest["_id"])}
        saved = await db.retest_states.find_one({"user_id": user.id, "subject_id": subject_id})
        if saved:
            return {"subject_id": subject_id, "state": saved.get("state", "available"),
                    "topics": saved.get("topics", await AssessmentService._retest_topics(user.id, subject_id, db)),
                    "reminder_at": saved.get("reminder_at")}
        return {"subject_id": subject_id, "state": "available",
                "topics": await AssessmentService._retest_topics(user.id, subject_id, db)}

    @staticmethod
    async def get_assessment_with_questions(
        assessment_id: str, user_id: str, db: AsyncIOMotorDatabase
    ) -> Optional[Assessment]:
        try:
            doc = await db.assessments.find_one(
                {"_id": oid(assessment_id), "user_id": user_id}
            )
        except Exception:
            return None
        return _build_assessment(doc)

    @staticmethod
    async def submit_assessment(
        assessment_id: str, user: User, payload: AssessmentSubmitRequest, db: AsyncIOMotorDatabase
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        assessment = await AssessmentService.get_assessment_with_questions(assessment_id, user.id, db)
        if not assessment:
            return None, "Assessment not found."
        if assessment.status == "completed":
            return None, "Assessment already submitted."

        now = datetime.now(timezone.utc)
        expires_at = as_utc(assessment.expires_at)
        is_expired = bool(expires_at and now > (expires_at + timedelta(seconds=45)))

        questions_by_qid = {q["question_id"]: q for q in assessment.questions}
        answers_dict = {a.question_id: a.selected_answer for a in payload.answers}

        total_correct = 0
        topic_counts: Dict[str, Dict[str, int]] = {}

        for qid, q in questions_by_qid.items():
            topic = q["topic"]
            if topic not in topic_counts:
                topic_counts[topic] = {"total": 0, "correct": 0}
            topic_counts[topic]["total"] += 1

            student_ans = answers_dict.get(qid)
            is_correct = False
            if student_ans:
                clean_student = student_ans.strip().lower()
                clean_correct = q["correct_answer"].strip().lower()
                if clean_student == clean_correct:
                    is_correct = True
                else:
                    try:
                        opts = q.get("options", [])
                        if clean_student in ["a", "b", "c", "d"]:
                            letter_idx = ord(clean_student) - ord("a")
                            if 0 <= letter_idx < len(opts) and opts[letter_idx].strip().lower() == clean_correct:
                                is_correct = True
                    except Exception:
                        pass

            if is_correct:
                total_correct += 1
                topic_counts[topic]["correct"] += 1

        total_q = len(assessment.questions)
        pct = round((total_correct / max(1, total_q)) * 100.0, 1)

        topic_stats = []
        topic_breakdown_items = []
        overall_trend = "stable"
        for top_name, counts in topic_counts.items():
            t_tot = counts["total"]
            t_cor = counts["correct"]
            t_pct = round((t_cor / max(1, t_tot)) * 100.0, 1)

            question_subject_id = next(
                (q.get("subject_id") for q in assessment.questions if q.get("topic") == top_name),
                assessment.subject_id,
            )
            prior = await db.topic_performance.find_one(
                {"user_id": user.id, "subject_id": question_subject_id, "topic": top_name}
            )
            prior_pct = float(prior.get("score_percentage", t_pct)) if prior else t_pct
            if assessment.assessment_type == "retest":
                blended_pct = AssessmentService.blend_topic_score(t_pct, prior_pct)
                trend = "improving" if t_pct > prior_pct else ("declining" if t_pct < prior_pct else "stable")
            else:
                blended_pct, trend = t_pct, "baseline"
            if assessment.assessment_type == "retest":
                overall_trend = trend
            if blended_pct >= 75.0:
                cat, prio, p_weight = "Strong", "Low", 0.5
            elif blended_pct >= 50.0:
                cat, prio, p_weight = "Moderate", "Medium", 1.0
            else:
                cat, prio, p_weight = "Needs Attention", "High", 1.5
            topic_stats.append({"topic": top_name, "percentage": blended_pct, "total": t_tot, "correct": t_cor})
            topic_breakdown_items.append({
                "topic": top_name, "total": t_tot, "correct": t_cor,
                "percentage": blended_pct, "category": cat, "priority": prio,
                "previous_percentage": prior_pct if assessment.assessment_type == "retest" else None,
                "difference": round(blended_pct - prior_pct, 1) if assessment.assessment_type == "retest" else None,
                "trend": trend if assessment.assessment_type == "retest" else None,
            })

            # Upsert TopicPerformance
            await db.topic_performance.update_one(
                {"user_id": user.id, "subject_id": question_subject_id, "topic": top_name},
                {"$set": {
                    "score_percentage": blended_pct,
                    "total_questions": t_tot,
                    "correct_questions": t_cor,
                    "knowledge_category": cat,
                    "priority_weight": p_weight,
                    "last_assessed_at": now,
                    "updated_at": now,
                    "trend": trend,
                    "previous_score_percentage": prior_pct if assessment.assessment_type == "retest" else None,
                    "last_retest_score_percentage": t_pct if assessment.assessment_type == "retest" else None,
                }, "$setOnInsert": {
                    "user_id": user.id,
                    "subject_id": question_subject_id,
                    "topic": top_name,
                }},
                upsert=True,
            )

        ai = get_ai_provider()
        subject_doc = await db.subjects.find_one({"_id": oid(assessment.subject_id)})
        subject_name = subject_doc["name"] if subject_doc else "Subject"

        ai_analysis = await ai.analyze_assessment(
            subject=subject_name,
            total_score=total_correct,
            total_questions=total_q,
            topic_stats=topic_stats,
        )

        final_status = "completed" if not is_expired else "expired"
        feedback = ai_analysis.get("feedback") or [
            f"Score: {pct:.1f}% ({total_correct}/{total_q}).",
            f"Prioritize {', '.join([x['topic'] for x in topic_breakdown_items if x['category'] == 'Needs Attention'][:2]) or 'steady practice'} next.",
            "Review explanations and schedule another check-in after your next completed study block.",
        ]
        await db.assessments.update_one(
            {"_id": oid(assessment.id)},
            {"$set": {
                "status": final_status,
                "score": total_correct,
                "percentage": pct,
                "completed_at": now,
                "knowledge_level": ai_analysis.get("overall_level", "Intermediate"),
                "analysis_json": json.dumps(ai_analysis),
                "retest_metadata": {**assessment.retest_metadata, "state": final_status, "trend": overall_trend if assessment.assessment_type == "retest" else "baseline"},
            }},
        )

        return {
            "assessment_id": assessment.id,
            "subject_name": subject_name,
            "status": final_status,
            "score": total_correct,
            "total_questions": total_q,
            "percentage": pct,
            "knowledge_level": ai_analysis.get("overall_level", "Intermediate"),
            "anti_cheat_warnings": assessment.anti_cheat_warnings,
            "topic_breakdown": topic_breakdown_items,
            "strengths": ai_analysis.get("strengths", []),
            "moderate_topics": ai_analysis.get("moderate_topics", []),
            "weak_topics": ai_analysis.get("weak_topics", []),
            "priority_topics": ai_analysis.get("priority_topics", []),
            "recommendations": ai_analysis.get("recommendations", []),
            "completed_at": now,
            "trend": overall_trend if assessment.assessment_type == "retest" else None,
            "feedback": feedback[:3],
        }, "Assessment evaluated successfully."

    @staticmethod
    async def log_anti_cheat_event(
        assessment_id: str, user: User, event_type: str, details: Optional[str], db: AsyncIOMotorDatabase
    ) -> int:
        result = await db.assessments.find_one_and_update(
            {"_id": oid(assessment_id), "user_id": user.id},
            {"$inc": {"anti_cheat_warnings": 1}},
            return_document=True,
        )
        if result:
            await db.focus_events.insert_one({
                "assessment_id": assessment_id,
                "user_id": user.id,
                "event_type": event_type,
                "details": details,
                "timestamp": datetime.now(timezone.utc),
            })
            return result.get("anti_cheat_warnings", 0)
        return 0
