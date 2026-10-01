"""
MongoDB async database layer using Motor.
Provides a single MongoClient, a typed DB accessor, and collection helpers.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from app.config import settings

# ── Module-level client (initialized in lifespan) ─────────────────────────────
_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_database() -> AsyncIOMotorDatabase:
    """Return the active Motor database instance."""
    if _db is None:
        raise RuntimeError("Database is not initialized. Call init_db() first.")
    return _db


def get_collection(name: str) -> AsyncIOMotorCollection:
    """Return a named collection from the active database."""
    return get_database()[name]


async def init_db() -> None:
    """Connect to MongoDB Atlas and create indexes."""
    global _client, _db
    _client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=10_000,
        connectTimeoutMS=10_000,
    )
    _db = _client[settings.MONGODB_DB_NAME]

    # ── Indexes ───────────────────────────────────────────────────────────────
    await _db.users.create_index("email", unique=True, sparse=True)
    await _db.users.create_index("mobile", unique=True, sparse=True)

    await _db.subjects.create_index("name", unique=True)

    await _db.user_subjects.create_index([("user_id", 1), ("subject_id", 1)], unique=True)

    await _db.assessments.create_index([("user_id", 1), ("status", 1)])
    await _db.assessments.create_index([("user_id", 1), ("subject_id", 1), ("assessment_type", 1), ("status", 1)])
    await _db.assessments.create_index(
        [("user_id", 1), ("subject_id", 1), ("assessment_type", 1), ("status", 1)],
        name="one_active_retest_per_subject",
        partialFilterExpression={"assessment_type": "retest", "status": "in_progress"},
    )
    await _db.assessments.create_index(
        [("user_id", 1), ("assessment_type", 1), ("retest_date", 1), ("retest_kind", 1)],
        name="one_daily_retest_per_date",
        unique=True,
        partialFilterExpression={"assessment_type": "retest", "retest_kind": "daily"},
    )

    await _db.topic_performance.create_index(
        [("user_id", 1), ("subject_id", 1), ("topic", 1)], unique=True
    )

    await _db.availability.create_index("user_id")

    await _db.academic_plans.create_index([("user_id", 1), ("status", 1)])

    await _db.timetable_entries.create_index([("user_id", 1), ("date", 1)])

    await _db.study_sessions.create_index([("user_id", 1), ("status", 1)])
    await _db.study_sessions.create_index([("user_id", 1), ("timetable_entry_id", 1), ("status", 1)])
    await _db.retest_states.create_index([("user_id", 1), ("subject_id", 1)], unique=True)

    await _db.checkpoints.create_index([("user_id", 1), ("status", 1)])

    await _db.notifications.create_index([("user_id", 1), ("is_read", 1)])

    await _db.ai_recommendations.create_index([("user_id", 1), ("is_dismissed", 1)])

    await _db.focus_events.create_index("user_id")


async def close_db() -> None:
    """Close the MongoDB client connection."""
    global _client
    if _client:
        _client.close()
        _client = None


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency: yields the active Motor database."""
    yield get_database()
