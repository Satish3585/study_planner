from app.routers.auth import router as auth_router
from app.routers.subjects import router as subjects_router
from app.routers.assessment import router as assessment_router
from app.routers.availability import router as availability_router
from app.routers.planning import router as planning_router
from app.routers.timetable import router as timetable_router
from app.routers.study_sessions import router as study_sessions_router
from app.routers.checkpoints import router as checkpoints_router
from app.routers.analytics import router as analytics_router
from app.routers.notifications import router as notifications_router

__all__ = [
    "auth_router",
    "subjects_router",
    "assessment_router",
    "availability_router",
    "planning_router",
    "timetable_router",
    "study_sessions_router",
    "checkpoints_router",
    "analytics_router",
    "notifications_router"
]
