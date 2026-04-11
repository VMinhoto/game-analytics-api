"""
Analytics endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.repositories.player import SQLAlchemyPlayerRepository
from app.schemas.player import (
    AnomalyRecord,
    ContinentBreakdown,
    ResourceStats,
)
from app.services.player import PlayerService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


async def _get_service(
    session: AsyncSession = Depends(get_session),
) -> PlayerService:
    repo = SQLAlchemyPlayerRepository(session)
    return PlayerService(repo)


@router.get("/resources", response_model=ResourceStats)
async def resource_statistics(
    service: PlayerService = Depends(_get_service),
):
    """Global resource statistics across all players."""
    return await service.resource_stats()


@router.get("/continents", response_model=list[ContinentBreakdown])
async def continent_breakdown(
    service: PlayerService = Depends(_get_service),
):
    """Per-continent resource and activity breakdown."""
    return await service.continent_breakdown()


@router.get("/anomalies", response_model=list[AnomalyRecord])
async def detect_anomalies(
    z_threshold: float = Query(
        default=None,
        ge=1.0,
        le=5.0,
        description="Z-score threshold (defaults to config value)",
    ),
    service: PlayerService = Depends(_get_service),
):
    """
    Flag players with statistically unusual resource levels.

    Lower threshold = more results (catches borderline cases).
    Higher threshold = fewer results (only extreme outliers).
    """
    threshold = z_threshold or get_settings().anomaly_z_threshold
    return await service.detect_anomalies(z_threshold=threshold)