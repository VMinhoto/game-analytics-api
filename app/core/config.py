"""
Application settings powered by pydantic-settings.

Values are loaded from environment variables (or a .env file),
which keeps secrets out of code and makes the app 12-Factor compliant.

Usage:
    from app.core.config import get_settings
    settings = get_settings()
    print(settings.database_url)
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central configuration.

    Every field maps to an environment variable with the same name
    (case-insensitive).  For example, ``DATABASE_URL`` can be set via
    ``export DATABASE_URL=...`` or in a ``.env`` file.
    """

    app_name: str = "Game Analytics API"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./game_analytics.db"

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # Analytics
    anomaly_z_threshold: float = 2.0

    # Redis (event-driven messaging)
    redis_url: str = "redis://localhost:6379/0"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — parsed once, reused everywhere."""
    return Settings()