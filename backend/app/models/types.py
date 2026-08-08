"""
app/models/types.py

Custom SQLAlchemy column type definitions for cross-database compatibility.

AutoJSON:
  - Uses standard JSON on SQLite (current default database)
  - Automatically upgrades to native JSONB on PostgreSQL when migrated
  - Supports indexing, containment operators (@>, ?), and GIN indexes on PostgreSQL
  - Zero application-level code changes required for the migration
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


class AutoJSON(sa.types.TypeDecorator):
    """
    JSON column type with automatic JSONB promotion on PostgreSQL.

    On SQLite  → stored as TEXT (JSON)
    On PostgreSQL → stored as native JSONB with binary storage and GIN indexing

    Usage::

        from app.models.types import AutoJSON

        input_features: Mapped[Optional[dict]] = mapped_column(AutoJSON, nullable=True)
    """

    impl = sa.JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: sa.engine.Dialect) -> sa.types.TypeEngine:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(sa.JSON())

    def process_bind_param(self, value: object, dialect: sa.engine.Dialect) -> object:
        return value

    def process_result_value(self, value: object, dialect: sa.engine.Dialect) -> object:
        return value
