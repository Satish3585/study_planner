from types import SimpleNamespace

import pytest

from app.models.assessment import Assessment
from app.routers.assessment import submit_assessment as submit_assessment_route
from app.schemas.assessment import AssessmentSubmitRequest
from app.services.assessment_service import AssessmentService
from app.services.planning_service import PlanningService
from app.utils.validators import is_valid_email


def test_topic_selection_uses_distinct_completed_non_break_pairs():
    entries = [
        {"status": "Completed", "activity_type": "Study", "subject_id": "s1", "topic": "Inheritance"},
        {"status": "Completed", "activity_type": "Study", "subject_id": "s1", "topic": "Inheritance"},
        {"status": "Skipped", "activity_type": "Study", "subject_id": "s1", "topic": "Generics"},
        {"status": "Completed", "activity_type": "Break", "subject_id": "s1", "topic": "Break"},
        {"status": "Completed", "activity_type": "Practice", "subject_id": "s2", "topic": "Calculus"},
    ]

    assert AssessmentService.select_completed_topic_pairs(entries) == [
        {"subject_id": "s1", "topic": "Inheritance"},
        {"subject_id": "s2", "topic": "Calculus"},
    ]


def test_retest_score_uses_weighted_average():
    assert AssessmentService.blend_topic_score(80, 40) == 64
    assert AssessmentService.blend_topic_score(50, 75) == 60


def test_email_requires_gmail_com_domain():
    assert is_valid_email("username@gmail.com")
    assert not is_valid_email("username@gmail.co")
    assert not is_valid_email("username@yahoo.com")


class _Assessments:
    async def find_one(self, query):
        return {
            "_id": "507f1f77bcf86cd799439011",
            "user_id": "user-1",
            "subject_id": "subject-1",
            "title": "Daily Retest",
            "assessment_type": "retest",
            "retest_date": query["retest_date"],
            "retest_kind": "daily",
            "status": "completed",
            "questions": [],
        }


class _Db:
    assessments = _Assessments()


@pytest.mark.asyncio
async def test_duplicate_daily_retest_returns_existing_assessment():
    assessment, message = await AssessmentService.start_daily_retest(
        SimpleNamespace(id="user-1"), "2026-09-30", _Db()
    )

    assert isinstance(assessment, Assessment)
    assert assessment.retest_date == "2026-09-30"
    assert "already exists" in message


@pytest.mark.asyncio
async def test_completed_retest_regenerates_with_completed_entries_preserved(monkeypatch):
    called = {}

    async def fake_submit(*args, **kwargs):
        return ({
            "assessment_id": "assessment-1",
            "subject_name": "Computer Science",
            "status": "completed",
            "score": 2,
            "total_questions": 3,
            "percentage": 66.7,
            "knowledge_level": "Intermediate",
            "anti_cheat_warnings": 0,
            "topic_breakdown": [],
            "strengths": [],
            "moderate_topics": [],
            "weak_topics": [],
            "priority_topics": [],
            "recommendations": [],
            "completed_at": None,
            "trend": "improving",
            "feedback": ["a", "b", "c"],
        }, "ok")

    async def fake_regenerate(*args, **kwargs):
        called.update(kwargs)
        return {}

    monkeypatch.setattr(AssessmentService, "submit_assessment", fake_submit)
    monkeypatch.setattr(PlanningService, "generate_plan_and_timetable", fake_regenerate)

    await submit_assessment_route(
        "assessment-1",
        AssessmentSubmitRequest(answers=[]),
        SimpleNamespace(id="user-1"),
        SimpleNamespace(),
    )

    assert called["preserve_completed"] is True
    assert called["days_ahead"] == 7
