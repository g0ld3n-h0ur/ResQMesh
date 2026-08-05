"""
app/schemas/base.py

Shared Pydantic v2 base schema classes used across all domain schemas.

Hierarchy
---------
BaseSchema
  └── IDSchema          (adds id: UUID)
        └── TimestampSchema  (adds created_at, updated_at)
              └── FullResponseSchema  (adds is_deleted — full audit response)

All domain Response schemas inherit from FullResponseSchema to ensure
ORM-serialised responses include the complete BaseModel field set.

model_config = ConfigDict(from_attributes=True) is set on BaseSchema and
inherited by all children — enabling direct ORM model → Pydantic serialisation
with model_validate(orm_instance).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """
    Root schema base with ORM compatibility enabled.

    All domain schemas should inherit from this class (or one of its
    subclasses) rather than directly from pydantic.BaseModel.
    """

    model_config = ConfigDict(
        from_attributes=True,       # ORM object → schema serialisation
        populate_by_name=True,      # allow both field name and alias
        str_strip_whitespace=True,  # strip leading/trailing whitespace
        use_enum_values=True,       # serialize enums as their .value string
    )


class IDSchema(BaseSchema):
    """Adds the UUID primary key field."""

    id: UUID = Field(..., description="UUID v4 primary key.")


class TimestampSchema(IDSchema):
    """Adds timezone-aware audit timestamps to the ID schema."""

    created_at: datetime = Field(..., description="UTC timestamp of record creation.")
    updated_at: datetime = Field(..., description="UTC timestamp of last update.")


class FullResponseSchema(TimestampSchema):
    """
    Complete base for all ORM response schemas.

    Includes id, created_at, updated_at, and the soft-delete flag.
    Every domain Response schema should inherit from this.
    """

    is_deleted: bool = Field(
        default=False,
        description="True when the record has been logically deleted.",
    )
