"""
Service layer — all business logic lives here.
"""

from app.repositories.base import AbstractPlayerRepository
from app.schemas.player import (
    AnomalyRecord,
    ContinentBreakdown,
    PaginatedResponse,
    PlayerSnapshot,
    PlayerSummary,
    ResourceStats,
)
from app.utils.anomaly import compute_z_scores


class PlayerService:
    """
    Orchestrates player-related business operations.

    Receives a repository via constructor injection.
    """

    def __init__(self, repository: AbstractPlayerRepository) -> None:
        self._repo = repository

    # -- Player operations -----------------------------------------------------

    async def get_player(self, player_id: int) -> PlayerSnapshot | None:
        """
        Get the latest snapshot for a player.

        Returns None if the player doesn't exist
        """
        row = await self._repo.get_latest_by_player_id(player_id)
        if row is None:
            return None
        return self._to_snapshot(row)

    async def list_players(
        self,
        *,
        page: int = 1,
        size: int = 20,
        continent: int | None = None,
        min_resources: int | None = None,
        has_captcha: bool | None = None,
        name_search: str | None = None,
    ) -> PaginatedResponse:
        """
        Paginated player list.

        Converts raw ORM objects to lightweight summaries — the list
        view doesn't need full snapshots with troop_info for every
        player.
        """
        offset = (page - 1) * size

        rows, total = await self._repo.list_players(
            offset=offset,
            limit=size,
            continent=continent,
            min_resources=min_resources,
            has_captcha=has_captcha,
            name_search=name_search,
        )

        items = [
            PlayerSummary(
                player_id=r.player_id,
                player_name=r.player_name,
                continent=r.continent,
                latest_snapshot=r.created_at,
                total_resources=r.total_resources(),
            )
            for r in rows
        ]

        pages = (total + size - 1) // size

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_player_history(
        self,
        player_id: int,
        *,
        limit: int = 50,
    ) -> list[PlayerSnapshot]:
        """Time-series snapshots for one player."""
        rows = await self._repo.get_player_history(player_id, limit=limit)
        return [self._to_snapshot(r) for r in rows]

    # -- Analytics -------------------------------------------------------------

    async def resource_stats(self) -> ResourceStats:
        """Global resource statistics."""
        data = await self._repo.get_resource_stats()
        return ResourceStats(**data)

    async def continent_breakdown(self) -> list[ContinentBreakdown]:
        """Per-continent resource breakdown."""
        rows = await self._repo.get_continent_breakdown()
        return [ContinentBreakdown(**r) for r in rows]

    async def detect_anomalies(
        self,
        *,
        z_threshold: float = 2.0,
    ) -> list[AnomalyRecord]:
        """
        Find players with statistically unusual resource levels.
        """
        # Get the data.
        snapshots = await self._repo.get_all_latest_snapshots()
        if not snapshots:
            return []

        # Extract the values we want to analyze.
        totals = [s.total_resources() for s in snapshots]

        # Run the statistical analysis.
        results = compute_z_scores(totals, threshold=z_threshold)

        # Build response objects for anomalous players only.
        anomalies: list[AnomalyRecord] = []
        for snapshot, result in zip(snapshots, results):
            if result.is_anomaly:
                anomalies.append(
                    AnomalyRecord(
                        player_id=snapshot.player_id,
                        player_name=snapshot.player_name,
                        continent=snapshot.continent,
                        total_resources=result.value,
                        z_score=result.z_score,
                        reason=result.reason,
                    )
                )

        # Sort by severity (most extreme first).
        anomalies.sort(key=lambda a: abs(a.z_score), reverse=True)

        return anomalies

    # -- Private helpers -------------------------------------------------------

    @staticmethod
    def _to_snapshot(row) -> PlayerSnapshot:
        """
        Convert an ORM object to a PlayerSnapshot schema.
        """
        return PlayerSnapshot(
            id=row.id,
            created_at=row.created_at,
            player_id=row.player_id,
            player_name=row.player_name,
            premium_points_nr=row.premium_points_nr,
            wood_nr=row.wood_nr,
            clay_nr=row.clay_nr,
            iron_nr=row.iron_nr,
            merch_available_nr=row.merch_available_nr,
            merch_available_total_nr=row.merch_available_total_nr,
            troop_info=row.troop_info,
            continent=row.continent,
            incomings=row.incomings,
            has_captcha=row.has_captcha,
            total_resources=row.total_resources(),
        )