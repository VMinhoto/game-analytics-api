"""
Shared test fixtures.

This conf file sets up the testing environment with:
    - In-memory SQLite DB — fast, isolated, no external dependencies.
    - Each test gets a fresh database via the ``db_session`` fixture.
    - The ``async_client`` fixture wires a test HTTP client to a test
      app with the real DB swapped for our test DB.
    - ``seed_data`` inserts sample rows for tests that need data.

"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base, get_session
from app.main import create_app
from app.models.player import MultiInfo


TEST_DB_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def db_engine():
    """Create a fresh in-memory database engine."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Yield a fresh async session for direct DB operations in tests."""
    factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(db_engine):
    """
    HTTP client wired to a test app with overridden DB.

    This is the standard FastAPI testing pattern: swap the real
    database for a test database at the dependency level.
    """
    app = create_app()
    factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_data(db_session: AsyncSession):
    """Insert sample data for tests that need it."""
    rows = [
        MultiInfo(
            player_id=1, player_name="Alice", premium_points_nr=100,
            wood_nr=5000, clay_nr=4000, iron_nr=3000,
            continent=55, incomings=2, has_captcha=False,
        ),
        MultiInfo(
            player_id=2, player_name="Bob", premium_points_nr=50,
            wood_nr=1000, clay_nr=800, iron_nr=600,
            continent=55, incomings=0, has_captcha=True,
        ),
        MultiInfo(
            player_id=3, player_name="Charlie", premium_points_nr=200,
            wood_nr=50000, clay_nr=40000, iron_nr=30000,
            continent=44, incomings=10, has_captcha=False,
        ),
        # Second snapshot for Alice (newer data).
        MultiInfo(
            player_id=1, player_name="Alice", premium_points_nr=120,
            wood_nr=6000, clay_nr=5000, iron_nr=4000,
            continent=55, incomings=3, has_captcha=False,
        ),
    ]
    db_session.add_all(rows)
    await db_session.commit()
    return rows