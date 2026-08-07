"""
ml/predict.py

AI / ML prediction module — framework skeleton + flood prediction integration.

This module loads serialised scikit-learn models from disk using joblib
and exposes prediction functions for each model domain.  Models are loaded
once on first access via the ModelRegistry and cached for the process lifetime.

DO NOT MODIFY THE ModelRegistry CLASS OR EXISTING STUBS.
The predict_flood() function is the only addition made in Phase 5.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("ml.predict")

# ---------------------------------------------------------------------------
# Model storage directory
# ---------------------------------------------------------------------------
MODEL_DIR = Path(__file__).parent / "models"


# ---------------------------------------------------------------------------
# Model loader skeleton
# ---------------------------------------------------------------------------

class ModelRegistry:
    """
    Lazy-loading registry for trained scikit-learn models.

    Models are loaded on first access and cached in memory for the
    lifetime of the application process.
    """

    def __init__(self) -> None:
        self._models: dict[str, Any] = {}

    def load(self, model_name: str) -> Any:
        """
        Load a serialised model from disk and cache it.

        Tries {model_name}.joblib first, then {model_name}.pkl as fallback.
        joblib can deserialise both formats.

        Args:
            model_name: Filename (without extension) of the serialised model.

        Returns:
            The deserialised scikit-learn estimator.

        Raises:
            FileNotFoundError: If no matching model file exists.
            RuntimeError: If the model file cannot be deserialised.
        """
        if model_name not in self._models:
            # Search order: .joblib → .pkl
            candidates = [
                MODEL_DIR / f"{model_name}.joblib",
                MODEL_DIR / f"{model_name}.pkl",
            ]
            model_path = next((p for p in candidates if p.exists()), None)

            if model_path is None:
                searched = ", ".join(str(p) for p in candidates)
                raise FileNotFoundError(
                    f"Model '{model_name}' not found. Searched: {searched}. "
                    "Train and serialise the model before loading."
                )

            import joblib  # noqa: PLC0415 — imported lazily to avoid startup overhead
            try:
                self._models[model_name] = joblib.load(model_path)
                logger.info("Loaded model '%s' from %s", model_name, model_path)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to deserialise model '{model_name}' from {model_path}: {exc}"
                ) from exc

        return self._models[model_name]

    def is_loaded(self, model_name: str) -> bool:
        """Return True if the named model is currently loaded in memory."""
        return model_name in self._models


# Module-level model registry instance
registry = ModelRegistry()


# ---------------------------------------------------------------------------
# Prediction function stubs
# ---------------------------------------------------------------------------

def predict_disaster_risk(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Predict the disaster risk level for a given geographic area.

    Args:
        input_data: Feature dictionary (region, historical data, weather, etc.).

    Returns:
        Prediction result dict with keys: risk_level, confidence, details.
    """
    raise NotImplementedError(
        "predict_disaster_risk is not yet implemented. "
        "Train a model and implement inference logic in Phase 3."
    )


def predict_resource_needs(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Estimate resource requirements for an active disaster scenario.

    Args:
        input_data: Feature dictionary (disaster type, affected population, etc.).

    Returns:
        Prediction result dict with estimated resource quantities per category.
    """
    raise NotImplementedError(
        "predict_resource_needs is not yet implemented. "
        "Train a model and implement inference logic in Phase 3."
    )


def predict_affected_population(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Estimate the number of people affected by a disaster event.

    Args:
        input_data: Feature dictionary (disaster location, magnitude, radius, etc.).

    Returns:
        Prediction result dict with estimated affected population count.
    """
    raise NotImplementedError(
        "predict_affected_population is not yet implemented. "
        "Train a model and implement inference logic in Phase 3."
    )


# ---------------------------------------------------------------------------
# Flood prediction (Phase 5)
# ---------------------------------------------------------------------------

# Feature column order expected by the trained flood model.
# Must match the column order used during model training exactly.
FLOOD_FEATURE_COLUMNS = [
    "rainfall_mm",
    "river_level_m",
    "soil_moisture_pct",
    "temperature_c",
    "humidity_pct",
    "previous_flood_events",
    "elevation_m",
    "population_density",
]

# Risk level thresholds — applied to the raw probability output
_RISK_THRESHOLDS = [
    (0.75, "critical"),
    (0.50, "high"),
    (0.25, "medium"),
    (0.0,  "low"),
]

# Model name (file: ml/models/flood_model.joblib or flood_model.pkl)
_FLOOD_MODEL_NAME = "flood_model"


def _probability_to_risk(probability: float) -> str:
    """Map a [0, 1] probability to a human-readable risk label."""
    for threshold, label in _RISK_THRESHOLDS:
        if probability >= threshold:
            return label
    return "low"


def predict_flood(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Predict flood occurrence probability and risk level.

    Loads the flood model on first call (cached for subsequent calls).

    Expected input_data keys
    ------------------------
    - rainfall_mm          : float  — recent rainfall in millimetres
    - river_level_m        : float  — current river water level in metres
    - soil_moisture_pct    : float  — soil moisture percentage (0–100)
    - temperature_c        : float  — ambient temperature in Celsius
    - humidity_pct         : float  — relative humidity percentage (0–100)
    - previous_flood_events: int    — number of historical flood events
    - elevation_m          : float  — terrain elevation in metres
    - population_density   : float  — people per sq km

    Returns
    -------
    dict with keys:
        prediction  : int    — 1 (flood likely) or 0 (flood unlikely)
        confidence  : float  — model confidence in range [0.0, 1.0]
        risk_level  : str    — "low" | "medium" | "high" | "critical"
        probability : float  — raw flood probability from the model
        model       : str    — model identifier string

    Raises
    ------
    FileNotFoundError : model file not found in ml/models/
    ValueError        : required feature missing from input_data
    RuntimeError      : model inference failure
    """
    import numpy as np  # noqa: PLC0415

    # Validate all required features are present
    missing = [col for col in FLOOD_FEATURE_COLUMNS if col not in input_data]
    if missing:
        raise ValueError(
            f"Missing required flood model input features: {missing}. "
            f"Required: {FLOOD_FEATURE_COLUMNS}."
        )

    # Load model (cached after first call)
    model = registry.load(_FLOOD_MODEL_NAME)

    # Build feature array in the exact training column order
    try:
        feature_values = [float(input_data[col]) for col in FLOOD_FEATURE_COLUMNS]
        features = np.array(feature_values).reshape(1, -1)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"All flood model features must be numeric. Error: {exc}"
        ) from exc

    # Run inference
    try:
        prediction: int = int(model.predict(features)[0])
        # Use predict_proba if available (classifier), else use raw output as probability
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(features)[0]
            # probability of the positive class (flood = 1)
            probability: float = float(proba[1]) if len(proba) > 1 else float(proba[0])
        else:
            # Regression model — treat raw output as probability, clamp to [0, 1]
            raw = float(model.predict(features)[0])
            probability = max(0.0, min(1.0, raw))
            prediction = 1 if probability >= 0.5 else 0
    except Exception as exc:
        raise RuntimeError(
            f"Flood model inference failed: {exc}"
        ) from exc

    risk_level = _probability_to_risk(probability)

    logger.info(
        "Flood prediction: prediction=%s probability=%.4f risk=%s",
        prediction,
        probability,
        risk_level,
    )

    return {
        "prediction": prediction,
        "confidence": round(probability if prediction == 1 else 1.0 - probability, 4),
        "risk_level": risk_level,
        "probability": round(probability, 4),
        "model": _FLOOD_MODEL_NAME,
    }


# ---------------------------------------------------------------------------
# Allocation priority + relief units prediction
#
# Trained by ml/train_priority_model.py on the hackathon-provided
# disaster_relief_resource_allocation.csv (200k rows). Both models are full
# scikit-learn Pipelines (imputation + one-hot encoding + estimator saved
# together), so inference here is just "build a one-row DataFrame with the
# training column names and call .predict()" — no hand-rolled encoding to
# keep in sync with training.
# ---------------------------------------------------------------------------

from ml.train_priority_model import FEATURE_COLUMNS as _PRIORITY_FEATURE_COLUMNS  # noqa: E402

_PRIORITY_CLASSIFIER_NAME = "priority_classifier"
_RELIEF_UNITS_REGRESSOR_NAME = "relief_units_regressor"


def _build_priority_input_row(input_data: dict[str, Any]) -> Any:
    import pandas as pd  # noqa: PLC0415

    missing = [col for col in _PRIORITY_FEATURE_COLUMNS if col not in input_data]
    if missing:
        raise ValueError(
            f"Missing required priority model input features: {missing}. "
            f"Required: {_PRIORITY_FEATURE_COLUMNS}."
        )
    row = {col: input_data[col] for col in _PRIORITY_FEATURE_COLUMNS}
    return pd.DataFrame([row])


def predict_allocation_priority(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Predict resource allocation priority (Low/Medium/High/Critical) for a
    disaster incident, via the RandomForestClassifier trained on the
    hackathon-provided dataset.

    Returns
    -------
    dict with keys:
        allocation_priority   : str   — predicted class label
        confidence             : float — probability of the predicted class
        class_probabilities    : dict  — probability per class
        model                   : str

    Raises
    ------
    FileNotFoundError : model file not found — run ml/train_priority_model.py first.
    ValueError        : required feature missing from input_data.
    RuntimeError       : model inference failure.
    """
    row = _build_priority_input_row(input_data)
    model = registry.load(_PRIORITY_CLASSIFIER_NAME)

    try:
        prediction = model.predict(row)[0]
        proba = model.predict_proba(row)[0]
        classes = list(model.classes_)
        confidence = float(proba[classes.index(prediction)])
    except Exception as exc:
        raise RuntimeError(f"Priority classifier inference failed: {exc}") from exc

    logger.info("Priority prediction: %s (confidence=%.4f)", prediction, confidence)

    return {
        "allocation_priority": str(prediction),
        "confidence": round(confidence, 4),
        "class_probabilities": {cls: round(float(p), 4) for cls, p in zip(classes, proba)},
        "model": _PRIORITY_CLASSIFIER_NAME,
    }


def predict_relief_units(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Predict the recommended number of relief units for a disaster incident,
    via the RandomForestRegressor trained on the hackathon-provided dataset.

    Returns
    -------
    dict with keys:
        recommended_relief_units : int
        model                      : str

    Raises
    ------
    FileNotFoundError : model file not found — run ml/train_priority_model.py first.
    ValueError        : required feature missing from input_data.
    RuntimeError       : model inference failure.
    """
    row = _build_priority_input_row(input_data)
    model = registry.load(_RELIEF_UNITS_REGRESSOR_NAME)

    try:
        prediction = float(model.predict(row)[0])
    except Exception as exc:
        raise RuntimeError(f"Relief units regressor inference failed: {exc}") from exc

    recommended_units = round(max(0.0, prediction))
    logger.info("Relief units prediction: %s", recommended_units)

    return {
        "recommended_relief_units": recommended_units,
        "model": _RELIEF_UNITS_REGRESSOR_NAME,
    }
