"""
SQLAlchemy implementation of the player repository.

This is the ONLY module in the project that contains database queries.
Every other module works through the abstract interface.  If you ever
need to swap databases, you write a new implementation of
AbstractPlayerRepository — nothing else changes.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import MultiInfo
from app.repositories.base import AbstractPlayerRepository


class SQLAlchemyPlayerRepository(AbstractPlayerRepository):
    """Concrete repository backed by an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- helpers ---------------------------------------------------------------

    def _latest_per_player_subquery(self):
        """
        Subquery that finds the most recent row per player.

        Uses MAX(id) grouped by player_id.  Since id is an
        auto-incrementing primary key, the highest id for a given
        player is always the newest snapshot.

        This is the "get latest snapshot" pattern discussed earlier.
        """
        return (
            select(
                MultiInfo.player_id,
                func.max(MultiInfo.id).label("max_id"),
            )
            .group_by(MultiInfo.player_id)
            .subquery()
        )

    # -- single record reads ---------------------------------------------------

    async def get_by_id(self, record_id: int) -> MultiInfo | None:
        result = await self._session.execute(
            select(MultiInfo).where(MultiInfo.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_by_player_id(self, player_id: int) -> MultiInfo | None:
        result = await self._session.execute(
            select(MultiInfo)
            .where(MultiInfo.player_id == player_id)
            .order_by(MultiInfo.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # -- list with filters + pagination ----------------------------------------

    async def list_players(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        continent: int | None = None,
        min_resources: int | None = None,
        has_captcha: bool | None = None,
        name_search: str | None = None,
    ) -> tuple[list[MultiInfo], int]:
        """Paginated, filterable player list (latest snapshot per player)."""

        # Step 1: Get the latest snapshot id for each player.
        latest = self._latest_per_player_subquery()

        # Step 2: Join multi_info to that subquery so we only get
        # the latest row per player.
        query = select(MultiInfo).join(
            latest,
            (MultiInfo.player_id == latest.c.player_id)
            & (MultiInfo.id == latest.c.max_id),
        )

        # Step 3: Apply optional filters dynamically.
        # This pattern — building the query conditionally — is very
        # common in real APIs where users can filter by any combination
        # of fields.
        if continent is not None:
            query = query.where(MultiInfo.continent == continent)
        if has_captcha is not None:
            query = query.where(MultiInfo.has_captcha == has_captcha)
        if name_search:
            query = query.where(
                MultiInfo.player_name.ilike(f"%{name_search}%")
            )
        if min_resources is not None:
            query = query.where(
                (MultiInfo.wood_nr + MultiInfo.clay_nr + MultiInfo.iron_nr)
                >= min_resources
            )

        # Step 4: Count total matching rows (before pagination).
        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        # Step 5: Apply pagination and ordering.
        query = (
            query
            .order_by(MultiInfo.player_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(query)
        rows = list(result.scalars().all())

        return rows, total

    # -- history ---------------------------------------------------------------

    async def get_player_history(
        self,
        player_id: int,
        *,
        limit: int = 50,
    ) -> list[MultiInfo]:
        result = await self._session.execute(
            select(MultiInfo)
            .where(MultiInfo.player_id == player_id)
            .order_by(MultiInfo.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # -- analytics -------------------------------------------------------------

    async def get_resource_stats(self) -> dict[str, Any]:
        """Global resource statistics."""
        total_expr = MultiInfo.wood_nr + MultiInfo.clay_nr + MultiInfo.iron_nr

        result = await self._session.execute(
            select(
                func.count(func.distinct(MultiInfo.player_id)).label(
                    "total_players"
                ),
                func.avg(MultiInfo.wood_nr).label("avg_wood"),
                func.avg(MultiInfo.clay_nr).label("avg_clay"),
                func.avg(MultiInfo.iron_nr).label("avg_iron"),
                func.avg(total_expr).label("avg_total"),
                func.max(total_expr).label("max_total"),
                func.min(total_expr).label("min_total"),
            )
        )
        row = result.one()
        return {
            "total_players": row.total_players,
            "avg_wood": round(float(row.avg_wood or 0), 2),
            "avg_clay": round(float(row.avg_clay or 0), 2),
            "avg_iron": round(float(row.avg_iron or 0), 2),
            "avg_total_resources": round(float(row.avg_total or 0), 2),
            "max_total_resources": row.max_total or 0,
            "min_total_resources": row.min_total or 0,
        }

    async def get_continent_breakdown(self) -> list[dict[str, Any]]:
        """Per-continent aggregates."""
        total_expr = MultiInfo.wood_nr + MultiInfo.clay_nr + MultiInfo.iron_nr

        result = await self._session.execute(
            select(
                MultiInfo.continent,
                func.count(func.distinct(MultiInfo.player_id)).label(
                    "player_count"
                ),
                func.avg(MultiInfo.wood_nr).label("avg_wood"),
                func.avg(MultiInfo.clay_nr).label("avg_clay"),
                func.avg(MultiInfo.iron_nr).label("avg_iron"),
                func.avg(total_expr).label("avg_total"),
                func.avg(MultiInfo.premium_points_nr).label("avg_premium"),
                func.sum(MultiInfo.incomings).label("total_incomings"),
            )
            .group_by(MultiInfo.continent)
            .order_by(MultiInfo.continent)
        )
        return [
            {
                "continent": row.continent,
                "player_count": row.player_count,
                "avg_wood": round(float(row.avg_wood or 0), 2),
                "avg_clay": round(float(row.avg_clay or 0), 2),
                "avg_iron": round(float(row.avg_iron or 0), 2),
                "avg_total_resources": round(float(row.avg_total or 0), 2),
                "avg_premium_points": round(float(row.avg_premium or 0), 2),
                "total_incomings": row.total_incomings or 0,
            }
            for row in result.all()
        ]

    async def get_all_latest_snapshots(self) -> list[MultiInfo]:
        """Every player's latest snapshot — for anomaly detection."""
        latest = self._latest_per_player_subquery()
        result = await self._session.execute(
            select(MultiInfo).join(
                latest,
                (MultiInfo.player_id == latest.c.player_id)
                & (MultiInfo.id == latest.c.max_id),
            )
        )
        return list(result.scalars().all())