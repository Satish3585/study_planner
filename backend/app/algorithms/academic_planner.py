from typing import List, Dict, Any
from app.algorithms.priority_engine import PriorityEngine

class AcademicPlanner:
    """Decides WHAT the student should study.
    Analyzes all subjects and topics for the student, determines academic priorities,
    and sets study goals and activity types (Study, Practice, Revision).
    """
    def __init__(self, priority_engine: PriorityEngine = None):
        self.priority_engine = priority_engine or PriorityEngine()

    def build_academic_plan(
        self,
        subjects: List[Dict[str, Any]],
        topic_performances: List[Dict[str, Any]],
        total_weekly_study_hours: float = 21.0
    ) -> Dict[str, Any]:
        """Generates an academic plan with topic targets and activity suggestions."""
        total_weekly_minutes = int(total_weekly_study_hours * 60)
        
        # Prepare topic items
        all_topics = []
        for tp in topic_performances:
            all_topics.append({
                "subject_id": tp.get("subject_id"),
                "subject_name": tp.get("subject_name", "Subject"),
                "topic": tp.get("topic"),
                "score_percentage": tp.get("score_percentage", 50.0),
            })
            
        # Fallback if student has not completed any assessments yet
        if not all_topics:
            for sub in subjects:
                sub_name = sub.get("name", "Subject")
                sub_id = sub.get("id")
                all_topics.extend([
                    {"subject_id": sub_id, "subject_name": sub_name, "topic": f"Foundations of {sub_name}", "score_percentage": 40.0},
                    {"subject_id": sub_id, "subject_name": sub_name, "topic": f"Core Concepts of {sub_name}", "score_percentage": 60.0},
                    {"subject_id": sub_id, "subject_name": sub_name, "topic": f"Applied Practice in {sub_name}", "score_percentage": 50.0},
                ])

        weighted_topics = self.priority_engine.calculate_topic_weights(all_topics)
        distributed_topics = self.priority_engine.calculate_study_distribution(weighted_topics, total_weekly_minutes)

        # Assign activity types based on category
        for t in distributed_topics:
            cat = t.get("category")
            trend = t.get("trend")
            previous = t.get("previous_score_percentage")
            current = t.get("score_percentage", 0)
            why_changed = (
                f"{t['topic']} improved {previous:.0f}% -> {current:.0f}%, moved to revision."
                if trend == "improving" and previous is not None else
                f"{t['topic']} declined to {current:.0f}%, increased time and priority."
                if trend == "declining" else None
            )
            if cat == "Needs Attention":
                t["activity_type"] = "Study"
                t["reason"] = f"Diagnostic assessment identified {t['topic']} as needing attention."
            elif cat == "Moderate":
                t["activity_type"] = "Practice"
                t["reason"] = f"Practice required to master {t['topic']} concepts."
            else:
                t["activity_type"] = "Revision"
                t["reason"] = f"Spaced revision to maintain high proficiency in {t['topic']}."
            if why_changed:
                t["reason"] = why_changed

        return {
            "title": "Continuous Mastery Academic Plan",
            "total_allocated_hours": round(total_weekly_minutes / 60.0, 1),
            "allocation_ratio": {"weak_ratio": 0.60, "moderate_ratio": 0.30, "strong_ratio": 0.10},
            "topics": distributed_topics
        }
