"""
app/services/severity_prediction_service.py

Business logic for the resource-allocation priority prediction module —
trained on the hackathon-provided disaster_relief_resource_allocation.csv
dataset (see ml/train_priority_model.py).

Mirrors prediction_service.py's structure and error-translation pattern
exactly, but calls two models (classifier + regressor) and merges their
results into one response.

Error handling
--------------
503 Service Unavailable : model file(s) not found — run ml/train_priority_model.py
422 Unprocessable Entity: missing or invalid features
500 Internal Server Error: inference failure
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status

from ml.predict import predict_allocation_priority, predict_relief_units

logger = logging.getLogger("app.services.severity_prediction_service")

# ---------------------------------------------------------------------------
# Feature field names (must match ml.train_priority_model.FEATURE_COLUMNS)
# ---------------------------------------------------------------------------
_PRIORITY_FEATURES = [
    "population_affected",
    "households_affected",
    "infrastructure_damage_score",
    "nearest_relief_center_distance_km",
    "available_volunteers",
    "medical_teams_available",
    "food_stock_kg",
    "water_stock_liters",
    "shelter_capacity",
    "funding_available_usd",
    "vulnerability_index",
    "ngo_present",
    "government_response_active",
    "disaster_type",
    "severity_level",
    "accessibility_status",
    "communication_status",
    "power_status",
]


def run_priority_prediction(features: dict[str, Any]) -> dict[str, Any]:
    """
    Validate allocation-priority prediction input and run both trained models.

    Args:
        features: Dict of feature values keyed by feature name. See
                  _PRIORITY_FEATURES for the required keys.

    Returns:
        dict merging predict_allocation_priority() and predict_relief_units()
        output: allocation_priority, confidence, class_probabilities,
        recommended_relief_units.

    Raises:
        HTTPException 503: a model file was not found on disk.
        HTTPException 422: missing or non-numeric feature values.
        HTTPException 500: inference failure inside either ML model.
    """
    missing = [f for f in _PRIORITY_FEATURES if f not in features]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Missing required priority model input features.",
                "missing_fields": missing,
                "required_fields": _PRIORITY_FEATURES,
            },
        )

    try:
        priority_result = predict_allocation_priority(features)
        relief_units_result = predict_relief_units(features)

    except FileNotFoundError as exc:
        logger.error("Priority/relief-units model not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The priority prediction models are not available. "
                "Run 'python ml/train_priority_model.py' with the hackathon "
                "dataset in ml/datasets/ first."
            ),
        ) from exc

    except ValueError as exc:
        logger.warning("Priority prediction input validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        logger.exception("Priority/relief-units model inference error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Priority prediction inference failed. "
                "Please try again or contact the platform administrator."
            ),
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected error during priority prediction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during priority prediction.",
        ) from exc

    result = {
        "allocation_priority": priority_result["allocation_priority"],
        "confidence": priority_result["confidence"],
        "class_probabilities": priority_result["class_probabilities"],
        "recommended_relief_units": relief_units_result["recommended_relief_units"],
        "priority_model": priority_result["model"],
        "relief_units_model": relief_units_result["model"],
    }
    logger.info(
        "Priority prediction complete: priority=%s relief_units=%s",
        result.get("allocation_priority"),
        result.get("recommended_relief_units"),
    )
    return result
