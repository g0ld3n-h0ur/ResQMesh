"""
app/models/csr.py

CSR disaster-relief program tracking model.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Float, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CSRProgram(BaseModel):
    """
    CSR Disaster Relief Program tracking model.
    """

    __tablename__ = "csr_programs"

    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    program_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    total_contribution_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    allocated_amount_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    utilized_amount_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    beneficiary_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coverage_area: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
