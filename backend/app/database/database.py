"""
app/database/database.py

SQLAlchemy engine and declarative base configuration.

The engine is created once and shared across the application.
Use `Base` as the parent class for all SQLAlchemy model definitions.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, MappedColumn

from app.core.config import settings


# ---------------------------------------------------------------------------
# SQLite-specific: enforce foreign key constraints at the connection level
# ---------------------------------------------------------------------------
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection: object, connection_record: object) -> None:
    """Enable WAL mode and foreign key enforcement for every SQLite connection."""
    if "sqlite" in settings.DATABASE_URL.lower():
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    # connect_args is SQLite-specific; harmless for other engines
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """
    Shared declarative base for all SQLAlchemy ORM models.

    All model classes in app/models/ must inherit from this class so that
    Alembic can auto-detect schema changes via `target_metadata`.
    """
