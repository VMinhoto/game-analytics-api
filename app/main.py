"""
Application factory.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import analytics, players
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown lifecycle.

    Code before ``yield`` runs at startup.
    Code after ``yield`` runs at shutdown.
    """
    settings = get_settings()
    print(f"Starting {settings.app_name} (debug={settings.debug})")
    yield
    print("Shutting down gracefully")


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "REST API for game player analytics. "
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # Register routers with API version prefix.
    app.include_router(players.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")

    # Health check
    @app.get("/health", tags=["Infrastructure"])
    async def health_check():
        return {"status": "healthy", "app": settings.app_name}

    return app


# The app object that uvicorn imports.
# ``uvicorn app.main:app --reload``
app = create_app()