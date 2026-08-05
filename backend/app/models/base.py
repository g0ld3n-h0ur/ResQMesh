"""
app/models/base.py

Abstract base model for all SQLAlchemy ORM models in the application.

BaseModel composition:
  - UUID v4 primary key (cross-database via sqlalchemy.Uuid)
  - Timezone-aware created_at / updated_at (via TimestampMixin)
  - Soft-delete support via is_deleted flag (via SoftDeleteMixin)
  - Inherits from the shared declarative Base (app/database/database.py)

Every domain model must inherit from BaseModel — never directly from Base.

MRO: DomainModel → BaseModel → TimestampMixin → SoftDeleteMixin → Base
"""

from __future__ import annotations

import uuid

from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class BaseModel(TimestampMixin, SoftDeleteMixin, Base):
    """
    Abstract parent for every ORM model.

    Do not instantiate directly. All domain models inherit from this class
    to gain a consistent primary key, timestamps, and soft-delete behaviour.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key, auto-generated at INSERT.",
    )
