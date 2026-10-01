import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.database import init_db
from app.routers import (
    auth_router,
    subjects_router,
    assessment_router,
    availability_router,
    planning_router,
    timetable_router,
    study_sessions_router,
    checkpoints_router,
    analytics_router,
    notifications_router
)
from app.routers.retest import router as retest_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("study_planner")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI Study Planner database tables...")
    await init_db()
    logger.info(f"Database initialized. AI Provider: {settings.AI_PROVIDER.upper()}")
    if settings.OTP_DEMO_MODE:
        logger.info("Demo OTP Mode is ENABLED. OTP codes will be printed in server logs.")
    yield
    logger.info("Shutting down AI Study Planner backend.")

app = FastAPI(
    title="AI Personalized Study Planner API",
    description="Adaptive AI study system built around the continuous learning loop: Assess → Analyze → Plan → Study → Checkpoint → Adapt",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clean, user-facing error handling (Section 36)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err["loc"] if loc != "body"])
        msg = err["msg"]
        errors.append(f"{field}: {msg}" if field else msg)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "; ".join(errors)}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again shortly."}
    )

# Health checks
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Personalized Study Planner",
        "ai_provider": settings.AI_PROVIDER,
        "environment": settings.APP_ENV
    }

# Register API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(assessment_router, prefix="/api")
app.include_router(availability_router, prefix="/api")
app.include_router(planning_router, prefix="/api")
app.include_router(timetable_router, prefix="/api")
app.include_router(study_sessions_router, prefix="/api")
app.include_router(checkpoints_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(retest_router, prefix="/api")
