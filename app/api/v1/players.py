"""
Player endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.player import SQLAlchemyPlayerRepository
from app.schemas.player import PaginatedResponse, PlayerSnapshot
from app.services.player import PlayerService

router = APIRouter(prefix="/players", tags=["Players"])


# ---------------------------------------------------------------------------
# Dependency: builds a fully wired service for each request
# ---------------------------------------------------------------------------

async def _get_service(
    session: AsyncSession = Depends(get_session),
) -> PlayerService:
    """
    This is where the layers connect.

    FastAPI calls get_session → we get a database session.
    We wrap it in a repository → data access is abstracted.
    We pass the repository to the service → business logic is ready.

    Each request gets its own session → its own repo → its own service.
    No shared state between requests.
    """
    repo = SQLAlchemyPlayerRepository(session)
    return PlayerService(repo)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=PaginatedResponse)
async def list_players(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    continent: int | None = Query(default=None, description="Filter by continent"),
    min_resources: int | None = Query(default=None, ge=0),
    has_captcha: bool | None = Query(default=None),
    name_search: str | None = Query(default=None, max_length=100),
    service: PlayerService = Depends(_get_service),
):
    """
    List players with pagination and optional filters.

    All filters are optional — omit any to skip that filter.
    """
    return await service.list_players(
        page=page,
        size=size,
        continent=continent,
        min_resources=min_resources,
        has_captcha=has_captcha,
        name_search=name_search,
    )


@router.get("/{player_id}", response_model=PlayerSnapshot)
async def get_player(
    player_id: int,
    service: PlayerService = Depends(_get_service),
):
    """Get the latest snapshot for a specific player."""
    player = await service.get_player(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.get("/{player_id}/history", response_model=list[PlayerSnapshot])
async def get_player_history(
    player_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    service: PlayerService = Depends(_get_service),
):
    """Historical snapshots for a player — resource trends over time."""
    history = await service.get_player_history(player_id, limit=limit)
    if not history:
        raise HTTPException(status_code=404, detail="Player not found")
    return history