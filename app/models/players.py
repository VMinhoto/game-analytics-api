"""
SQLAlchemy ORM model for the ``multi_info`` table.
 
Maps directly to the Supabase/Postgres schema.  Each row represents
one point-in-time snapshot of a player's game state.  Multiple rows
per player_id enable historical analysis (resource trends, troop
changes over time).
"""



from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, Boolean, SmallInteger, Text
from sqlalchemy.dialects.postgresql import JSON

from app.core.database import Base

class MultiInfo(Base):
    """
    One snapshot of a player's game state at a point in time.
 
    Mapped columns use SQLAlchemy 2.0's ``Mapped[]`` syntax, which
    provides type hints that IDEs and linters understand — no more
    guessing whether a column is nullable or what type it returns.
    """

    __tablename__ = "multi_info"

    # Primary key — identity column in Postgres, autoincrement in SQLite.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    # Player identity
    player_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    player_name: Mapped[str] = mapped_column(Text, nullable=False)

    # Resources
    premium_points_nr: Mapped[int] = mapped_column(Integer, nullable=False)
    wood_nr: Mapped[int] = mapped_column(Integer, nullable=False)
    clay_nr: Mapped[int] = mapped_column(Integer, nullable=False)
    iron_nr: Mapped[int] = mapped_column(Integer, nullable=False)

    # Merchant
    merch_available_nr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    merch_available_total_nr: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Troops — stored as JSON for flexibility.
    troop_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Location and status
    continent: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    incomings: Mapped[int] = mapped_column(Integer, nullable=False)
    has_captcha: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def total_resources(self) -> int:
        """Helper method to calculate total resources in this snapshot."""
        return self.wood_nr + self.clay_nr + self.iron_nr
    
    def __repr__(self) -> str:
        """Readable string representation for debugging."""
        return (
            f"<MultiInfo id={self.id} player={self.player_name!r} "
            f"continent={self.continent}>"
        )