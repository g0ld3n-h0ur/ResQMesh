"""
app/core/config.py

Centralised application configuration.
All settings are loaded from environment variables (or .env file)
using Pydantic v2 BaseSettings for type-safety and validation.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------------------------------------------------------------------------
    # Application
    # ---------------------------------------------------------------------------
    APP_NAME: str = "AI Disaster Relief Coordination Platform"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Production-ready FastAPI backend for an AI-powered "
        "Disaster Relief Coordination Platform."
    )
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # ---------------------------------------------------------------------------
    # API
    # ---------------------------------------------------------------------------
    API_V1_PREFIX: str = "/api/v1"

    # ---------------------------------------------------------------------------
    # CORS — stored as a raw comma-separated string from the env file.
    # Use the `cors_origins_list` property to get the parsed list.
    # ---------------------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS_ORIGINS as a parsed list of origin strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # ---------------------------------------------------------------------------
    # Database
    # ---------------------------------------------------------------------------
    DATABASE_URL: str = "sqlite:///./disaster_relief.db"

    # ---------------------------------------------------------------------------
    # Security / JWT
    # ---------------------------------------------------------------------------
    SECRET_KEY: str = "change-this-secret-key-before-deploying"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---------------------------------------------------------------------------
    # Logging
    # ---------------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    # ---------------------------------------------------------------------------
    # ML
    # ---------------------------------------------------------------------------
    ML_MODEL_PATH: str = "ml/models"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of application settings."""
    return Settings()


# Module-level convenience alias
settings: Settings = get_settings()
