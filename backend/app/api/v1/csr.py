"""
app/api/v1/csr.py

CSR Relief Tracking & Donor Transparency router.

Prefix: /api/v1/csr
Tags: CSR & Donor Transparency
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.csr import CSRProgram
from app.models.delivery import ProofOfDelivery
from app.utils.response import success_response

router = APIRouter(
    prefix="/csr",
    tags=["CSR & Donor Transparency"],
)


class CSRProgramCreate(BaseModel):
    organization_id: uuid.UUID = Field(...)
    program_name: str = Field(..., examples=["Clean Water Disaster Relief Initiative"])
    total_contribution_usd: float = Field(..., ge=0.0, examples=[100000.0])
    coverage_area: Optional[str] = Field("Coastal Flood Zone A")


class ProofOfDeliveryCreate(BaseModel):
    dispatched_quantity: int = Field(..., ge=0, examples=[1000])
    received_quantity: int = Field(..., ge=0, examples=[980])
    verified_quantity: int = Field(..., ge=0, examples=[980])
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)
    evidence_url: Optional[str] = Field(None)


@router.post("/programs", summary="Create CSR Relief Program")
async def create_csr_program(
    payload: CSRProgramCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    prog = CSRProgram(
        organization_id=payload.organization_id,
        program_name=payload.program_name,
        total_contribution_usd=payload.total_contribution_usd,
        allocated_amount_usd=payload.total_contribution_usd * 0.8,
        utilized_amount_usd=payload.total_contribution_usd * 0.5,
        beneficiary_count=int(payload.total_contribution_usd / 10.0),
        coverage_area=payload.coverage_area,
        status="ACTIVE",
    )
    db.add(prog)
    db.commit()
    db.refresh(prog)
    return success_response(data={"id": str(prog.id), "program_name": prog.program_name}, message="CSR program created successfully.")


@router.get("/programs", summary="List CSR Relief Programs")
async def list_csr_programs(
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    progs = db.query(CSRProgram).filter(CSRProgram.is_deleted == False).all()
    data = [
        {
            "id": str(p.id),
            "organization_id": str(p.organization_id),
            "program_name": p.program_name,
            "total_contribution_usd": p.total_contribution_usd,
            "allocated_amount_usd": p.allocated_amount_usd,
            "utilized_amount_usd": p.utilized_amount_usd,
            "remaining_amount_usd": p.total_contribution_usd - p.utilized_amount_usd,
            "beneficiary_count": p.beneficiary_count,
            "coverage_area": p.coverage_area,
            "status": p.status,
        }
        for p in progs
    ]
    return success_response(data=data, message="CSR programs retrieved.")


@router.get("/transparency/public-summary", summary="Public Donor Transparency View (Aggregated & Privacy-Preserving)")
async def get_public_transparency_summary(
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    progs = db.query(CSRProgram).filter(CSRProgram.is_deleted == False).all()
    total_funding = sum(p.total_contribution_usd for p in progs)
    total_utilized = sum(p.utilized_amount_usd for p in progs)
    total_beneficiaries = sum(p.beneficiary_count for p in progs)

    deliveries = db.query(ProofOfDelivery).filter(ProofOfDelivery.is_deleted == False).all()
    verified_count = sum(1 for d in deliveries if d.status == "VERIFIED")

    return success_response(
        data={
            "public_aggregated_transparency": {
                "total_csr_contributions_usd": total_funding,
                "total_deployed_usd": total_utilized,
                "total_remaining_usd": total_funding - total_utilized,
                "total_beneficiaries_served": total_beneficiaries,
                "verified_deliveries_count": verified_count,
                "active_programs_count": len(progs),
                "privacy_notice": "Citizen identity and personal address details are strictly redacted for privacy protection.",
            }
        },
        message="Public transparency aggregate summary retrieved.",
    )


@router.post("/proof-of-delivery", summary="Submit Proof of Delivery with discrepancy calculation")
async def create_proof_of_delivery(
    payload: ProofOfDeliveryCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    discrepancy = payload.dispatched_quantity - payload.received_quantity
    pod_status = "VERIFIED" if discrepancy == 0 else "DISCREPANCY"

    pod = ProofOfDelivery(
        dispatched_quantity=payload.dispatched_quantity,
        received_quantity=payload.received_quantity,
        verified_quantity=payload.verified_quantity,
        discrepancy_quantity=discrepancy,
        latitude=payload.latitude,
        longitude=payload.longitude,
        evidence_url=payload.evidence_url,
        status=pod_status,
    )
    db.add(pod)
    db.commit()
    db.refresh(pod)

    return success_response(
        data={
            "id": str(pod.id),
            "dispatched": pod.dispatched_quantity,
            "received": pod.received_quantity,
            "verified": pod.verified_quantity,
            "discrepancy": pod.discrepancy_quantity,
            "status": pod.status,
        },
        message=f"Proof of delivery recorded. Discrepancy: {discrepancy} units. Status: {pod_status}.",
    )
