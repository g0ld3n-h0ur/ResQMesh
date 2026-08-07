# ResQMesh Backend

FastAPI backend for the ResQMesh disaster relief coordination platform. See the
[root README](../README.md) for the full picture of what the platform does and
how to run the whole stack — this file covers the backend specifically.

**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · SQLite · Alembic · scikit-learn · JWT auth

---

## What's actually in here

This is a working backend, not a skeleton — 70 API routes across 16 routers, 15
service modules, 9 database entities, and two independently trained ML
pipelines. The sections below describe what exists today.

## Architecture

Layered, with a strict one-way dependency direction:

```
API layer (app/api/v1/)        FastAPI routes — request/response only, no business logic
    │
Service layer (app/services/)  All business logic, validation, and error translation
    │
Model layer (app/models/)      SQLAlchemy ORM entities
    │
Database (app/database/)       Engine, session factory, SQLite
```

- Routes call services; services call the ORM. Routes never touch the database directly.
- Every write path validates via a Pydantic schema (`app/schemas/`) before it reaches a service.
- Auth/RBAC is dependency-injected (`app/core/permissions.py`) — role checks live in the route signature, not scattered through handler bodies.
- ML inference is a separate concern entirely (`ml/`), called by services but with no FastAPI/DB knowledge of its own.

## Project structure

```
backend/
├── app/
│   ├── api/v1/                 16 routers — see "API surface" below
│   ├── core/
│   │   ├── config.py            Pydantic Settings (reads .env)
│   │   ├── security.py          JWT + bcrypt password hashing
│   │   ├── roles.py              Role hierarchy
│   │   └── permissions.py        require_role() dependency factory + named aliases
│   ├── database/
│   │   ├── database.py           Engine + declarative Base
│   │   ├── session.py            SessionLocal + get_db() dependency
│   │   └── seed.py                Demo data seeding (see root README)
│   ├── dependencies/auth.py     get_current_user / get_current_active_user
│   ├── middleware/
│   │   ├── logging.py            Structured request/response access logs
│   │   └── rate_limit.py          In-memory rate limiting (login, public SOS submit)
│   ├── models/                  9 SQLAlchemy entities — see "Data model" below
│   ├── schemas/                 Pydantic request/response schemas, one file per domain
│   ├── services/                15 modules — all business logic lives here
│   ├── utils/
│   │   ├── constants.py          Tags, pagination defaults
│   │   ├── response.py           Standard {success, message, data, errors} envelope
│   │   └── geo.py                 Haversine distance
│   └── main.py                  App factory, middleware/router registration, lifespan
├── ml/
│   ├── predict.py                ModelRegistry (lazy-load + cache) + all inference functions
│   ├── train_sensor_model.py     Trains the flood-risk model (synthetic data, generated in-script)
│   ├── train_priority_model.py   Trains the priority/relief-units models (real hackathon dataset)
│   ├── datasets/                  Gitignored — drop the hackathon CSV here before training
│   └── models/                    Gitignored — trained .pkl files land here
├── alembic/                      Migration environment
├── tests/                        Stub only — no test coverage yet (see "Testing" below)
├── requirements.txt
├── Dockerfile / docker-compose.yml
└── .env.example
```

## Data model

9 core entities (`app/models/`), all soft-delete-aware (`is_deleted` flag, never hard-deleted):

| Entity | Purpose |
|---|---|
| `User` | One of 5 roles: government, ngo, volunteer, hospital, citizen. bcrypt-hashed password. |
| `Disaster` | The central entity — every other module hangs off a disaster. |
| `Resource` | Relief inventory item (food, water, medical kits, generators…) with total/available quantity. |
| `Shelter` | Physical facility with capacity + live occupancy. |
| `Hospital` | Medical facility with bed/ICU/ambulance/blood/oxygen capacity. |
| `EmergencyReport` | Citizen-submitted SOS incident; anonymous submission allowed. |
| `Assignment` | Links a volunteer, NGO, hospital, *or* resource to a disaster with a status lifecycle — the cross-org coordination mechanism. |
| `Notification` | Role- or user-targeted alert. |
| `Prediction` | Stored AI prediction output tied to a disaster. |

## API surface

Full interactive reference at `/docs` (Swagger) or `/redoc` once the server is running.
Routers, by prefix:

| Prefix | Tag | Notes |
|---|---|---|
| `/auth` | Authentication | Login (OAuth2 password flow → JWT), register per role, refresh, me |
| `/disasters` | Disasters | CRUD + search + `need-scores` + `distribution-priority` |
| `/resources` | Resources | CRUD + allocate/release + `allocation-suggestions` |
| `/shelters` | Shelters | CRUD + check-in/check-out |
| `/hospitals` | Hospitals | CRUD + bed availability updates |
| `/reports` | Reports | CRUD + public `/emergency` submission + verify |
| `/assignments` | Volunteer¹ | Cross-org assignment CRUD + status transitions |
| `/dashboard` | Dashboard | Aggregated KPI/statistics endpoints |
| `/notifications` | Notifications | CRUD + mark-read |
| `/prediction` | AI Prediction | `/predict` (flood) + `/predict-priority` (allocation priority/relief units) |
| `/external-data` | External Data | `/situational-feed` — live weather + earthquakes |
| `/users` | Users | Minimal role-filtered user directory, for assignee pickers |
| `/government`, `/ngo`, `/hospital`, `/citizens` | — | Registered, tagged, and empty — role-portal stubs, no real endpoints yet |

¹ `assignments.py`'s router lives in `app/api/v1/volunteer.py` for historical reasons — the tag says "Volunteer" but the endpoints serve Government/NGO/Volunteer alike.

## The ML subsystem

Two independent, unrelated pipelines share the `ml/` directory and the same
`ModelRegistry` loader pattern (lazy-load from disk on first request, cached
in memory for the process lifetime):

**Flood risk** (`train_sensor_model.py` → `flood_model.pkl`) — a
`RandomForestRegressor` trained on 10,000 rows of synthetic sensor data
generated by a physics-inspired formula (not real historical records). Takes
8 environmental inputs, outputs a flood probability and risk tier.

**Allocation priority + relief units** (`train_priority_model.py` →
`priority_classifier.pkl` + `relief_units_regressor.pkl`) — a
`RandomForestClassifier` and `RandomForestRegressor`, both full scikit-learn
`Pipeline`s (imputation + one-hot encoding + estimator saved together, so
inference never has to hand-roll encoding logic), trained on 200,000 real
incident records from a hackathon-provided dataset. Neither model file nor
the training dataset is committed to git — see the root README for how to
train them locally.

## Setup / running

See the root README's "Backend setup" section for the full walkthrough
(venv, dependencies, `.env`, seeding, training the ML models). Short version:

```bash
python -m venv .venv
source .venv/bin/activate        # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
cp .env.example .env
python -m app.database.seed
python ml/train_sensor_model.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment variables

| Variable | Default | Notes |
|---|---|---|
| `ENVIRONMENT` | `development` | |
| `DEBUG` | `true` | Enables SQLAlchemy query echo |
| `DATABASE_URL` | `sqlite:///./disaster_relief.db` | |
| `SECRET_KEY` | *(placeholder)* | JWT signing secret — startup logs a warning if left unchanged |
| `ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated |
| `LOG_LEVEL` | `INFO` | |
| `API_V1_PREFIX` | `/api/v1` | |
| `ML_MODEL_PATH` | `ml/models` | |

## Database migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
```

## Docker

```bash
docker compose up --build
```

## Testing

`tests/` is currently a stub (`__init__.py` only) — `pytest`, `pytest-asyncio`,
and `httpx` are pinned as dependencies but no test suite has been written yet.
This is an honest gap, not an oversight to gloss over.

## Known limitations

- Blocking synchronous DB calls happen inside `async def` route handlers throughout — fine at demo traffic, would stall the event loop under real concurrent load.
- No eager-loading (`selectinload`/`joinedload`) on some relationship-heavy queries — N+1 risk on larger datasets.
- Rate limiting is in-process memory, not distributed — fine for a single instance, not for a multi-worker deployment.
- The four role-portal stub routers (`government.py`, `ngo.py`, `hospital.py`, `citizen.py`) are registered and tagged but have zero real endpoints.
