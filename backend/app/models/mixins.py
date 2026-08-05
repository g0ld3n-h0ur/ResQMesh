"""
app/models/mixins.py

Reusable SQLAlchemy 2.x column mixins.

Mixins defined here are inherited by BaseModel and applied to every table:
  - TimestampMixin  → created_at, updated_at (timezone-aware, auto-managed)
  - SoftDeleteMixin → is_deleted flag (soft delete pattern)

Both are pure Python mixin classes — they do NOT inherit from DeclarativeBase,
which allows SQLAlchemy's declarative system to copy their Mapped columns into
each concrete child model.

Indexes on created_at are applied at the mixin level so every table that
inherits from BaseModel automatically gains a query-performance index on the
creation timestamp, satisfying the requirement for created_at indexing without
repeating the definition per model.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Provides timezone-aware created_at and updated_at columns.

    - created_at: Set once at INSERT, never modified.
    - updated_at: Set at INSERT, automatically refreshed at every UPDATE
                  via the SQLAlchemy onupdate hook (Python-side).
    - Both columns are indexed to support time-range queries efficiently.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="UTC timestamp when the record was created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=False,  # updated_at queried less frequently than created_at
        doc="UTC timestamp of the most recent update to the record.",
    )


class SoftDeleteMixin:
    """
    Provides is_deleted column for non-destructive logical deletion.

    Application layer must filter `is_deleted == False` in all active-record
    queries. The index allows the DB to skip deleted rows efficiently.
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="True when the record has been logically deleted.",
    )
