# Game Analytics API

A production-ready REST API for game player analytics, built with **FastAPI**, **SQLAlchemy 2.0**, and **PostgreSQL**. Features a layered architecture with the Repository pattern, event-driven messaging via Redis, statistical anomaly detection, and a comprehensive async test suite.

## Architecture

The project follows a strict **layered architecture** where each layer depends only on the one below it through abstractions, making every component independently testable and swappable.

```
  ┌──────────────────────────────────┐
  │       API Layer (FastAPI)        │  ← HTTP handling, validation
  ├──────────────────────────────────┤
  │        Service Layer             │  ← Business logic, analytics
  │            │          │          │
  │      Event Bus ──► Redis Pub/Sub │  ← Async messaging
  ├──────────────────────────────────┤
  │      Repository Layer (ABC)      │  ← Data access abstraction
  ├────────────────┬─────────────────┤
  │   PostgreSQL   │     SQLite      │  ← Swappable backends
  └────────────────┴─────────────────┘
```

### Design decisions

- **Repository pattern** decouples business logic from the database — swap Postgres for SQLite (or any store) without touching service code. This is an application of the Dependency Inversion Principle.
- **Service layer** keeps API routes thin. All logic lives in testable service classes that accept repository abstractions via constructor injection.
- **Event-driven messaging** with an internal event bus backed by Redis pub/sub. When a snapshot is recorded or an anomaly is detected, events are published asynchronously for downstream consumers.
- **Pydantic v2 schemas** enforce strict request/response contracts and auto-generate OpenAPI documentation.
- **Factory pattern** for the app (`create_app()`) enables different configurations for development, testing, and production.

## Tech stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (async, ASGI) |
| ORM | SQLAlchemy 2.0 with async sessions |
| Validation | Pydantic v2 |
| Database | PostgreSQL via asyncpg (prod) / SQLite via aiosqlite (test) |
| Messaging | Redis pub/sub |
| Testing | pytest + httpx (async) |
| Containerization | Docker + docker-compose |

## Getting started

### Prerequisites

- Python 3.11+
- PostgreSQL (or use SQLite for local development)
- Redis (for event-driven features)

### Local development

```bash
git clone https://github.com/VMinhoto/game-analytics-api.git
cd game-analytics-api

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # Edit with your database credentials

uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### With Docker

```bash
docker-compose up --build
```

This starts the API, PostgreSQL, and Redis — everything needed to run the full stack.

### Running tests

```bash
pytest -v --cov=app
```

Tests use an in-memory SQLite database for speed and isolation. No external services required.

## API reference

### Players

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/players` | List players with pagination and filters |
| `GET` | `/api/v1/players/{player_id}` | Latest snapshot for a specific player |
| `GET` | `/api/v1/players/{player_id}/history` | Historical snapshots over time |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/analytics/resources` | Aggregate resource statistics |
| `GET` | `/api/v1/analytics/continents` | Per-continent breakdown |
| `GET` | `/api/v1/analytics/anomalies` | Detect unusual resource patterns via Z-score |

### Infrastructure

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |

### Query parameters

The players list endpoint supports filtering and pagination:

```
GET /api/v1/players?continent=55&min_resources=5000&page=1&size=20
```

- `continent` — filter by continent ID
- `min_resources` — minimum total resources (wood + clay + iron)
- `has_captcha` — filter by captcha status
- `name_search` — partial match on player name
- `page` / `size` — pagination controls

## Project structure

```
game-analytics-api/
├── app/
│   ├── main.py                  # App factory + lifespan
│   ├── core/
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── database.py          # Async engine + session factory
│   │   └── events.py            # Event bus + Redis pub/sub
│   ├── models/
│   │   └── player.py            # SQLAlchemy ORM model
│   ├── schemas/
│   │   └── player.py            # Pydantic request/response schemas
│   ├── repositories/
│   │   ├── base.py              # Abstract repository interface
│   │   └── player.py            # SQLAlchemy implementation
│   ├── services/
│   │   └── player.py            # Business logic + analytics
│   ├── api/v1/
│   │   ├── players.py           # Player CRUD endpoints
│   │   └── analytics.py         # Analytics endpoints
│   └── utils/
│       └── anomaly.py           # Z-score anomaly detection
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── unit/                    # Fast tests, mocked dependencies
│   └── integration/             # Tests against real database
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Configuration

All configuration is managed through environment variables, following the [12-Factor App](https://12factor.net/config) methodology. See `.env.example` for available options.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./game_analytics.db` | Database connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection for event bus |
| `DEBUG` | `false` | Enable debug mode and SQL logging |

## License

MIT