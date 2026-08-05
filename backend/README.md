# AI Disaster Relief Coordination Platform — Backend

**Version:** 1.0.0  
**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · SQLite · Alembic · Docker

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [Environment Variables](#environment-variables)
6. [API Documentation](#api-documentation)
7. [Database Migrations](#database-migrations)
8. [Docker](#docker)
9. [Testing](#testing)
10. [Development Guidelines](#development-guidelines)
11. [Roadmap](#roadmap)

---

## Overview

Production-ready FastAPI backend for an AI-powered Disaster Relief Coordination Platform.  
The platform coordinates government agencies, NGOs, volunteers, hospitals, and citizens
during disaster events using AI-driven predictions and real-time resource management.

---

## Architecture

The project follows **Clean Architecture** principles with a strict layered separation:

```
┌─────────────────────────────────────┐
│            API Layer                │  ← FastAPI routes (no business logic)
├─────────────────────────────────────┤
│          Service Layer              │  ← All business logic lives here
├─────────────────────────────────────┤
│          Database Layer             │  ← SQLAlchemy models & session
├─────────────────────────────────────┤
│        Configuration Layer          │  ← Pydantic Settings, env vars
├─────────────────────────────────────┤
│          Utility Layer              │  ← Helpers, constants, response builders
├─────────────────────────────────────┤
│            ML Layer                 │  ← scikit-learn inference (ml/)
└─────────────────────────────────────┘
```

**Key principles:**
- Routes call services — never the database directly.
- Services call models — never routes.
- Dependency injection via `fastapi.Depends`.
- No circular imports.
- All imports use the `app.` package prefix.

---

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py            # Authentication endpoints
│   │       ├── government.py      # Government portal
│   │       ├── ngo.py             # NGO portal
│   │       ├── volunteer.py       # Volunteer management
│   │       ├── hospital.py        # Hospital staff portal
│   │       ├── citizen.py         # Citizen self-service
│   │       ├── disasters.py       # Disaster lifecycle management
│   │       ├── reports.py         # Field incident reports
│   │       ├── prediction.py      # AI prediction endpoints
│   │       ├── dashboard.py       # Analytics dashboard
│   │       ├── resources.py       # Resource inventory
│   │       ├── shelters.py        # Shelter management
│   │       ├── hospitals.py       # Hospital registry
│   │       └── notifications.py   # Alert broadcasting
│   ├── core/
│   │   ├── config.py              # Pydantic Settings
│   │   ├── security.py            # JWT & password hashing
│   │   ├── roles.py               # UserRole enum
│   │   └── permissions.py         # RBAC dependency factories
│   ├── database/
│   │   ├── database.py            # Engine & DeclarativeBase
│   │   └── session.py             # Session factory & get_db()
│   ├── middleware/
│   │   └── logging.py             # Structured request logging
│   ├── models/                    # SQLAlchemy models (Phase 2)
│   ├── schemas/                   # Pydantic schemas (Phase 2)
│   ├── services/                  # Business logic services (Phase 2)
│   ├── utils/
│   │   ├── constants.py           # App-wide constants
│   │   ├── helpers.py             # Pure utility functions
│   │   └── response.py            # Standard response envelope
│   └── main.py                    # FastAPI app factory & system endpoints
├── ml/
│   └── predict.py                 # ML inference skeleton (Phase 3)
├── tests/                         # Test suite (Phase 2+)
├── alembic/                       # Migration environment (init separately)
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- pip
- (Optional) Docker & Docker Compose

### 1. Clone and navigate

```bash
git clone <repository-url>
cd AI-Disaster-Relief-Coordination-Platform/backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 5. Initialise Alembic migrations

```bash
alembic init alembic
# Then configure alembic/env.py to import app.database.database.Base and use settings.DATABASE_URL
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### 6. Run the development server

```bash
uvicorn app.main:app --reload
```

The API is now available at:

| Endpoint            | Description              |
|---------------------|--------------------------|
| `GET /`             | Platform metadata        |
| `GET /health`       | Health check             |
| `GET /docs`         | Swagger UI               |
| `GET /redoc`        | ReDoc                    |
| `GET /openapi.json` | OpenAPI schema           |

---

## Environment Variables

| Variable                      | Default                            | Description                              |
|-------------------------------|------------------------------------|------------------------------------------|
| `ENVIRONMENT`                 | `development`                      | Runtime environment                      |
| `DEBUG`                       | `true`                             | Enable SQLAlchemy query echo             |
| `DATABASE_URL`                | `sqlite:///./disaster_relief.db`   | SQLAlchemy connection string             |
| `SECRET_KEY`                  | *(must be changed)*                | JWT signing secret                       |
| `ALGORITHM`                   | `HS256`                            | JWT algorithm                            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                               | Access token TTL                         |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                                | Refresh token TTL                        |
| `CORS_ORIGINS`                | `http://localhost:3000`            | Comma-separated allowed CORS origins     |
| `LOG_LEVEL`                   | `INFO`                             | Python logging level                     |
| `API_V1_PREFIX`               | `/api/v1`                          | Global API version prefix                |
| `ML_MODEL_PATH`               | `ml/models`                        | Directory for serialised ML models       |

---

## API Documentation

Once the server is running, visit:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:**       [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON:**[http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

All endpoints are grouped by the tags below:

| Tag               | Prefix                       |
|-------------------|------------------------------|
| Authentication    | `/api/v1/auth`               |
| Government        | `/api/v1/government`         |
| NGO               | `/api/v1/ngo`                |
| Volunteer         | `/api/v1/volunteers`         |
| Hospital          | `/api/v1/hospital`           |
| Citizen           | `/api/v1/citizens`           |
| Disasters         | `/api/v1/disasters`          |
| Reports           | `/api/v1/reports`            |
| AI Prediction     | `/api/v1/prediction`         |
| Dashboard         | `/api/v1/dashboard`          |
| Resources         | `/api/v1/resources`          |
| Shelters          | `/api/v1/shelters`           |
| Hospitals         | `/api/v1/hospitals`          |
| Notifications     | `/api/v1/notifications`      |

---

## Database Migrations

This project uses **Alembic** for schema migrations.

```bash
# Create a new migration
alembic revision --autogenerate -m "describe change"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history --verbose
```

> **Note:** After initialising Alembic (`alembic init alembic`), update
> `alembic/env.py` to import `app.database.database.Base` as `target_metadata`
> and read `DATABASE_URL` from `app.core.config.settings`.

---

## Docker

### Development (hot-reload)

```bash
docker compose up --build
```

### Production build

```bash
docker compose -f docker-compose.yml up --build -d
```

The API will be available at `http://localhost:8000`.

---

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

---

## Development Guidelines

1. **Routes call services** — never access the DB directly from a route.
2. **Services call repositories / ORM** — never return SQLAlchemy ORM objects to routes.
3. **Use `Depends(get_db)`** for database session injection.
4. **Use `app.core.config.settings`** — never use `os.environ` directly.
5. **Use `app.utils.response`** — always return responses via the standard envelope helpers.
6. **No circular imports** — if module A imports module B, module B must not import module A.
7. **All imports must use** `from app.` prefix (no relative imports outside packages).

---

## Roadmap

| Phase | Description                                               | Status      |
|-------|-----------------------------------------------------------|-------------|
| 1     | Project skeleton, architecture, routing, DevOps           | ✅ Complete  |
| 2     | SQLAlchemy models, Pydantic schemas, service layer, auth  | 🔜 Planned  |
| 3     | ML model training, inference pipeline, prediction API     | 🔜 Planned  |
| 4     | Real-time WebSocket notifications, task queues            | 🔜 Planned  |
| 5     | Frontend integration, end-to-end testing, deployment      | 🔜 Planned  |
