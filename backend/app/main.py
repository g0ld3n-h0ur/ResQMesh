"""
app/main.py

FastAPI application factory and entry point.

This module:
  - Creates the FastAPI application instance with full OpenAPI metadata
  - Registers all v1 API routers under /api/v1
  - Mounts CORS, logging middleware
  - Configures structured logging
  - Exposes GET / and GET /health system endpoints
"""

import logging
import logging.config
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    auth,
    citizen,
    dashboard,
    disasters,
    government,
    hospital,
    hospitals,
    ngo,
    notifications,
    prediction,
    reports,
    resources,
    shelters,
    volunteer,
)
from app.core.config import settings
from app.middleware.logging import RequestLoggingMiddleware

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
LOGGING_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": settings.LOG_LEVEL,
        "handlers": ["console"],
    },
    "loggers": {
        "uvicorn": {"propagate": True},
        "uvicorn.error": {"propagate": True},
        "uvicorn.access": {"propagate": False},
        "app": {"propagate": True},
        "sqlalchemy.engine": {
            "level": "DEBUG" if settings.DEBUG else "WARNING",
            "propagate": True,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("app")


# ---------------------------------------------------------------------------
# Lifespan context (startup / shutdown hooks)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Code before `yield` runs at startup; code after `yield` runs at shutdown.
    Use this hook to initialise DB connections, load ML models, etc.
    """
    logger.info(
        "Starting %s v%s [%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
def create_application() -> FastAPI:
    """
    Construct and configure the FastAPI application.

    Returns:
        Fully configured FastAPI instance.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "System", "description": "System health and metadata endpoints."},
            {"name": "Authentication", "description": "User registration, login, and token management."},
            {"name": "Government", "description": "Government authority portal operations."},
            {"name": "NGO", "description": "Non-Governmental Organisation portal operations."},
            {"name": "Volunteer", "description": "Volunteer registration and assignment management."},
            {"name": "Hospital", "description": "Hospital staff portal operations."},
            {"name": "Citizen", "description": "Citizen-facing self-service operations."},
            {"name": "Disasters", "description": "Disaster event lifecycle management."},
            {"name": "Reports", "description": "Field incident and situation reports."},
            {"name": "AI Prediction", "description": "ML-powered risk and resource predictions."},
            {"name": "Dashboard", "description": "Aggregated analytics and summary dashboards."},
            {"name": "Resources", "description": "Relief resource inventory and allocation."},
            {"name": "Shelters", "description": "Emergency shelter management."},
            {"name": "Hospitals", "description": "Hospital registry and capacity coordination."},
            {"name": "Notifications", "description": "Alert and notification broadcasting."},
        ],
    )

    # -----------------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # Custom request / response logging middleware
    # -----------------------------------------------------------------------
    application.add_middleware(RequestLoggingMiddleware)

    # -----------------------------------------------------------------------
    # v1 Routers
    # -----------------------------------------------------------------------
    api_prefix = settings.API_V1_PREFIX

    application.include_router(auth.router, prefix=api_prefix)
    application.include_router(government.router, prefix=api_prefix)
    application.include_router(ngo.router, prefix=api_prefix)
    application.include_router(volunteer.router, prefix=api_prefix)
    application.include_router(hospital.router, prefix=api_prefix)
    application.include_router(citizen.router, prefix=api_prefix)
    application.include_router(disasters.router, prefix=api_prefix)
    application.include_router(reports.router, prefix=api_prefix)
    application.include_router(prediction.router, prefix=api_prefix)
    application.include_router(dashboard.router, prefix=api_prefix)
    application.include_router(resources.router, prefix=api_prefix)
    application.include_router(shelters.router, prefix=api_prefix)
    application.include_router(hospitals.router, prefix=api_prefix)
    application.include_router(notifications.router, prefix=api_prefix)

    return application


app: FastAPI = create_application()


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["System"], summary="Platform metadata")
async def root() -> dict:
    """
    Return basic platform metadata.

    Used by load balancers, monitoring tools, and the frontend to confirm
    the API is reachable.
    """
    return {
        "project": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health", tags=["System"], summary="Health check")
async def health_check() -> dict:
    """
    Lightweight health-check endpoint.

    Returns HTTP 200 when the application is running correctly.
    Extend this in Phase 2 to include DB and ML model liveness checks.
    """
    return {"status": "healthy"}
