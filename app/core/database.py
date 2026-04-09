"""
Async database engine and session factory.

Uses SQLAlchemy 2.0 async support.  The session factory is created once
at startup and yields per-request sessions via a FastAPI dependency —
ensuring each request gets its own transaction scope.

Key concepts for interviews:
    - Engine: manages a *pool* of database connections (not one connection).
    - Session: a unit of work — groups queries into a transaction.
    - Dependency injection: FastAPI's Depends() gives each request a fresh
      session, and cleans it up automatically when the request ends.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def build_engine(url: str | None = None):
    """
    Create an async engine.

    Accepts an optional *url* override so tests can inject an in-memory
    SQLite URL without touching environment variables.
    """
    db_url = url or get_settings().database_url

    connect_args: dict = {}
    if "sqlite" in db_url:
        connect_args["check_same_thread"] = False

    return create_async_engine(
        db_url,
        echo=get_settings().debug,
        connect_args=connect_args,
    )


engine = build_engine()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields one session per request.

    The ``async with`` block ensures the session is properly closed
    even if the request handler raises an exception.
    """
    async with async_session_factory() as session:
        yield session