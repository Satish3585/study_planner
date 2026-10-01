from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_db
from app.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.analytics import DashboardStatsResponse, AnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_data(
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    stats = await AnalyticsService.get_dashboard_stats(user, db)
    return DashboardStatsResponse(**stats)

@router.get("/progress", response_model=AnalyticsResponse)
async def get_progress_data(
    user: User = Depends(get_current_verified_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    analytics = await AnalyticsService.get_progress_analytics(user, db)
    return AnalyticsResponse(**analytics)
