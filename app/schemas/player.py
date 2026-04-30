"""
Pydantic v2 schemas for request validation and response serialization.

These are separate from ORM models on purpose — the API contract should
evolve independently of the database schema.  This prevents leaking
internal fields to consumers and lets us add computed fields, rename
things, or restructure responses without database migrations.

"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Response schemas — what the API sends back
# ---------------------------------------------------------------------------

class PlayerSnapshot(BaseModel):
    """Full point-in-time snapshot of a player."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    player_id: int
    player_name: str
    premium_points_nr: int
    wood_nr: int
    clay_nr: int
    iron_nr: int
    merch_available_nr: int | None = None
    merch_available_total_nr: int | None = None
    troop_info: dict | None = None
    continent: int
    incomings: int
    has_captcha: bool
    total_resources: int = Field(
        description="Computed: wood + clay + iron",
    )


class PlayerSummary(BaseModel):
    """Lightweight representation for list views.

    Intentionally omits heavy fields like troop_info — list endpoints
    should be fast, and consumers don't need full details for every
    player when browsing.
    """

    player_id: int
    player_name: str
    continent: int
    latest_snapshot: datetime
    total_resources: int
    total_pp: int


# ---------------------------------------------------------------------------
# Analytics schemas
# ---------------------------------------------------------------------------

class ResourceStats(BaseModel):
    """Aggregate resource statistics across all players."""

    total_players: int
    avg_wood: float
    avg_clay: float
    avg_iron: float
    avg_total_resources: float
    max_total_resources: int
    min_total_resources: int


class ContinentBreakdown(BaseModel):
    """Resource and activity aggregates for a single continent."""

    continent: int
    player_count: int
    avg_wood: float
    avg_clay: float
    avg_iron: float
    avg_total_resources: float
    avg_premium_points: float
    total_incomings: int


class AnomalyRecord(BaseModel):
    """A player flagged as statistically unusual."""

    player_id: int
    player_name: str
    continent: int
    total_resources: int
    z_score: float = Field(
        description="Standard deviations from the mean",
    )
    reason: str


# ---------------------------------------------------------------------------
# Request schemas — what the API accepts as input
# ---------------------------------------------------------------------------

class PlayerFilters(BaseModel):
    """Optional filters for the player list endpoint."""

    continent: int | None = None
    min_resources: int | None = None
    has_captcha: bool | None = None
    name_search: str | None = None


# ---------------------------------------------------------------------------
# Generic paginated response wrapper
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel):
    """Wraps any list endpoint with pagination metadata.

    Consumers need to know: how many total results exist, which page
    they're on, and how many pages there are — so they can build
    pagination controls (next/previous buttons, page numbers).
    """

    items: list
    total: int
    page: int
    size: int
    pages: int