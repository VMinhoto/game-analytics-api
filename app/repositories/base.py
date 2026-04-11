"""
Abstract repository interface.

This is the heart of the Repository Pattern and the key to making
the database swappable.  The service layer codes against THIS
abstraction — it never imports SQLAlchemy, never writes SQL, never
knows what database is underneath.

Why this matters (SOLID principles):
    - Single Responsibility: repositories handle data access only.
    - Open/Closed: add a new backend (e.g. MongoDB) by writing a new
      class, not by modifying existing code.
    - Dependency Inversion: high-level modules (services) depend on
      this abstraction, not on low-level database details.

Interview tip: if asked "why not just use SQLAlchemy directly in
your routes?", the answer is testability + flexibility.  With this
pattern, unit tests inject a fake repo (no DB needed), and swapping
from Postgres to DynamoDB means writing one new file — not rewriting
every service method.
"""

from abc import ABC, abstractmethod
from typing import Any


class AbstractPlayerRepository(ABC):
    """
    Contract that any player data store must fulfill.

    Implement this for Postgres, SQLite, a CSV file, or even a
    hardcoded dict — the service layer will never know the difference.
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