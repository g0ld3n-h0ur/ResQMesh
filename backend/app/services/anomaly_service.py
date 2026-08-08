"""
app/services/anomaly_service.py

Rule-based Anomaly Detection Service.
Strictly deterministic — NOT an ML model. Does not introduce additional datasets.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.models.anomaly import AnomalyRecord
from app.models.enums import AnomalySeverity
from app.models.delivery import ProofOfDelivery
from app.models.resource import Resource


def run_anomaly_checks(db: Session) -> List[Dict[str, Any]]:
    """
    Execute deterministic anomaly checks across resource stock and proof of delivery records.
    """
    anomalies: List[Dict[str, Any]] = []

    # Check 1: Proof of Delivery Discrepancies (delivered/verified > dispatched or discrepancy > 0)
    pod_records = db.query(ProofOfDelivery).filter(ProofOfDelivery.is_deleted == False).all()
    for pod in pod_records:
        if pod.received_quantity > pod.dispatched_quantity:
            desc = f"Received quantity ({pod.received_quantity}) exceeds dispatched quantity ({pod.dispatched_quantity}) for delivery {pod.id}"
            rec = AnomalyRecord(
                anomaly_type="DELIVERY_OVERAGE_DISCREPANCY",
                severity=AnomalySeverity.HIGH.value,
                explanation=desc,
                entity_type="ProofOfDelivery",
                entity_id=str(pod.id),
            )
            db.add(rec)
            anomalies.append({"type": rec.anomaly_type, "severity": rec.severity, "explanation": desc})

        if pod.discrepancy_quantity > 0:
            desc = f"Delivery discrepancy detected: {pod.discrepancy_quantity} units unverified for delivery {pod.id}"
            rec = AnomalyRecord(
                anomaly_type="UNVERIFIED_DELIVERY_DISCREPANCY",
                severity=AnomalySeverity.MEDIUM.value,
                explanation=desc,
                entity_type="ProofOfDelivery",
                entity_id=str(pod.id),
            )
            db.add(rec)
            anomalies.append({"type": rec.anomaly_type, "severity": rec.severity, "explanation": desc})

    # Check 2: Resource Inventory Negative or Over-Allocation
    resources = db.query(Resource).filter(Resource.is_deleted == False).all()
    for r in resources:
        qty = getattr(r, "quantity", 0)
        allocated = getattr(r, "allocated_quantity", 0)
        if qty < 0:
            desc = f"Negative inventory quantity ({qty}) detected for resource '{r.name}' ({r.id})"
            rec = AnomalyRecord(
                anomaly_type="NEGATIVE_INVENTORY",
                severity=AnomalySeverity.CRITICAL.value,
                explanation=desc,
                entity_type="Resource",
                entity_id=str(r.id),
            )
            db.add(rec)
            anomalies.append({"type": rec.anomaly_type, "severity": rec.severity, "explanation": desc})

        if allocated > qty and qty > 0:
            desc = f"Allocated quantity ({allocated}) exceeds total inventory ({qty}) for resource '{r.name}'"
            rec = AnomalyRecord(
                anomaly_type="RESOURCE_OVER_ALLOCATION",
                severity=AnomalySeverity.HIGH.value,
                explanation=desc,
                entity_type="Resource",
                entity_id=str(r.id),
            )
            db.add(rec)
            anomalies.append({"type": rec.anomaly_type, "severity": rec.severity, "explanation": desc})

    db.commit()
    return anomalies
