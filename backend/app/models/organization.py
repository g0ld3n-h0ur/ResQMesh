"""
app/models/organization.py

Multi-tenant organization model.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import SubscriptionTier
from app.models.types import AutoJSON


class Organization(BaseModel):
    """
    Multi-tenant Organization entity.

    Represents Government departments, NGOs, CSR foundations, or Hospitals.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    org_type: Mapped[str] = mapped_column(String(50), nullable=False, default="ngo")
    logo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    branding_config: Mapped[dict] = mapped_column(
        AutoJSON, nullable=False, default=dict
    )
    subscription_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SubscriptionTier.PILOT.value
    )
    enabled_features: Mapped[list] = mapped_column(
        AutoJSON, nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
