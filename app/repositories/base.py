"""
Abstract repository interface.
"""

from abc import ABC, abstractmethod
from typing import Any


class AbstractPlayerRepository(ABC):
    """
    Contract that any player data store must fulfill.
    """

    @abstractmethod
    async def get_by_id(self, record_id: int) -> Any | None:
        """Fetch a single snapshot by primary key."""

    @abstractmethod
    async def get_latest_by_player_id(self, player_id: int) -> Any | None:
        """Fetch the most recent snapshot for a given player."""

    @abstractmethod
    async def list_players(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        continent: int | None = None,
        min_resources: int | None = None,
        has_captcha: bool | None = None,
        name_search: str | None = None,
    ) -> tuple[list[Any], int]:
        """
        Return a page of latest-snapshot-per-player, plus total count.

        Returns (rows, total_count).
        """

    @abstractmethod
    async def get_player_history(
        self,
        player_id: int,
        *,
        limit: int = 50,
    ) -> list[Any]:
        """Historical snapshots for one player, newest first."""

    @abstractmethod
    async def get_resource_stats(self) -> dict[str, Any]:
        """Aggregate resource statistics across all latest snapshots."""

    @abstractmethod
    async def get_continent_breakdown(self) -> list[dict[str, Any]]:
        """Resource averages grouped by continent."""

    @abstractmethod
    async def get_all_latest_snapshots(self) -> list[Any]:
        """All players' latest snapshots — used for anomaly detection."""