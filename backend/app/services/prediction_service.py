"""
app/services/prediction_service.py

Business logic for the Prediction module.

Responsibilities
----------------
- Validate the incoming FloodPredictionRequest payload
- Build the feature dictionary expected by ml.predict.predict_flood()
- Call ml.predict.predict_flood() — the ML function handles model loading
  and caches the model after the first call via ModelRegistry
- Normalise and return the prediction result
- Translate ML errors (FileNotFoundError, ValueError, RuntimeError)
  into appropriate FastAPI HTTP exceptions

Model loading strategy
----------------------
The ModelRegistry in ml/predict.py is a module-level singleton.
The first call to registry.load("flood_model") deserialises the
model from disk; all subsequent calls return the cached object.
prediction_service.py itself does NOT cache anything — it delegates
all loading/caching to the registry.

Supported prediction types
--------------------------
- FLOOD  →  predict_flood()

Error handling
--------------
503 Service Unavailable : model file not found
422 Unprocessable Entity: missing or invalid features
500 Internal Server Error: inference failure
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status

from ml.predict import predict_flood

logger = logging.getLogger("app.services.prediction_service")

# ---------------------------------------------------------------------------
# Feature field names (must match ml.predict.FLOOD_FEATURE_COLUMNS)
# ---------------------------------------------------------------------------
_FLOOD_FEATURES = [
    "rainfall_mm",
    "river_level_m",
    "soil_moisture_pct",
    "temperature_c",
    "humidity_pct",
    "previous_flood_events",
    "elevation_m",
    "population_density",
]


def run_flood_prediction(features: dict[str, Any]) -> dict[str, Any]:
    """
    Validate flood prediction input and call the ML inference function.

    The model is loaded on the first call and cached by the ModelRegistry
    for all subsequent requests.

    Args:
        features: Dict of feature values keyed by feature name.
                  Required keys: rainfall_mm, river_level_m,
                  soil_moisture_pct, temperature_c, humidity_pct,
                  previous_flood_events, elevation_m, population_density.

    Returns:
        dict with keys: prediction, confidence, risk_level, probability, model.

    Raises:
        HTTPException 503: flood_model file not found on disk.
        HTTPException 422: missing or non-numeric feature values.
        HTTPException 500: inference failure inside the ML model.
    """
    # Service-layer feature presence check (before ML layer raises ValueError)
    missing = [f for f in _FLOOD_FEATURES if f not in features]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Missing required flood model input features.",
                "missing_fields": missing,
                "required_fields": _FLOOD_FEATURES,
            },
        )

    try:
        result = predict_flood(features)

    except FileNotFoundError as exc:
        logger.error("Flood model not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The flood prediction model is not available. "
                "Please ensure 'flood_model.joblib' or 'flood_model.pkl' "
                "exists in the ml/models/ directory."
            ),
        ) from exc

    except ValueError as exc:
        logger.warning("Flood prediction input validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        logger.exception("Flood model inference error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Flood prediction inference failed. "
                "Please try again or contact the platform administrator."
            ),
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected error during flood prediction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during flood prediction.",
        ) from exc

    logger.info(
        "Flood prediction complete: prediction=%s risk=%s confidence=%.4f",
        result.get("prediction"),
        result.get("risk_level"),
        result.get("confidence", 0.0),
    )
    return result
