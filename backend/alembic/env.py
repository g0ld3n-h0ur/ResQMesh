"""
Alembic migration environment configuration.

This module is executed by Alembic when running migration commands.
It connects to the database and sets the target metadata so Alembic
can auto-detect schema changes from SQLAlchemy models.

Usage:
    alembic revision --autogenerate -m "describe your change"
    alembic upgrade head
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Load application settings and declarative base
# ---------------------------------------------------------------------------
from app.core.config import settings
from app.database.database import Base

# Import all models here so Alembic includes them in autogenerate detection.
# Add new model imports below as they are created in Phase 2.
import app.models  # noqa: F401

# ---------------------------------------------------------------------------
# Alembic Config object (from alembic.ini)
# ---------------------------------------------------------------------------
config = context.config

# Override the sqlalchemy.url with the value from application settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configure Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migration mode
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This allows generating SQL scripts without a live DB connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migration mode
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode with an active DB connection.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
