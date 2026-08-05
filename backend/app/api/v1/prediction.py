"""
app/api/v1/prediction.py

AI Prediction router — complete production implementation.

Prefix : /api/v1/prediction
Tags   : AI Prediction

Endpoint map
------------
POST /predict  → Run a flood prediction (Government + NGO)

Supported prediction types
--------------------------
- flood  (only supported type in this phase)

Flow
----
1. Router receives request and validates payload via Pydantic
2. Router calls prediction_service.run_flood_prediction()
3. Service builds feature dict and calls ml.predict.predict_flood()
4. ml.predict loads model once via ModelRegistry (cached permanently)
5. Result is returned via success_response()

Permissions
-----------
Government + NGO only.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.core.permissions import require_role
from app.database.session import get_db
from app.models.enums import RoleEnum
from app.models.user import User
from app.services import prediction_service
from app.utils.constants import API_V1_TAG_PREDICTION
from app.utils.response import success_response

router = APIRouter(
    prefix="/prediction",
    tags=[API_V1_TAG_PREDICTION],
)

# ---------------------------------------------------------------------------
# Permission alias
# ---------------------------------------------------------------------------

_RequireGovOrNGO = Annotated[
    User,
    Depends(require_role(RoleEnum.GOVERNMENT, RoleEnum.NGO)),
]


# ---------------------------------------------------------------------------
# Request / Response schemas (local — no separate schema file needed)
# ---------------------------------------------------------------------------

class PredictionType(str, Enum):
    FLOOD = "flood"


class FloodPredictionRequest(BaseModel):
    """
    Input payload for the flood prediction endpoint.

    All eight features are required for the flood model.
    Values must be numeric — the model was trained on continuous features.
    """

    prediction_type: PredictionType = Field(
        PredictionType.FLOOD,
        description="Type of prediction to run. Currently only 'flood' is supported.",
    )

    # ---------- Flood model features ----------
    rainfall_mm: float = Field(
        ...,
        ge=0.0,
        description="Recent rainfall in millimetres (>= 0).",
        examples=[120.5],
    )
    river_level_m: float = Field(
        ...,
        ge=0.0,
        description="Current river water level in metres (>= 0).",
        examples=[4.2],
    )
    soil_moisture_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Soil moisture percentage (0–100).",
        examples=[78.3],
    )
    temperature_c: float = Field(
        ...,
        description="Ambient temperature in Celsius.",
        examples=[31.0],
    )
    humidity_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Relative humidity percentage (0–100).",
        examples=[88.5],
    )
    previous_flood_events: int = Field(
        ...,
        ge=0,
        description="Number of historical flood events in this region (>= 0).",
        examples=[3],
    )
    elevation_m: float = Field(
        ...,
        description="Terrain elevation in metres above sea level.",
        examples=[12.0],
    )
    population_density: float = Field(
        ...,
        ge=0.0,
        description="Population density in people per square kilometre (>= 0).",
        examples=[2450.0],
    )

    @model_validator(mode="after")
    def validate_flood_type(self) -> "FloodPredictionRequest":
        if self.prediction_type != PredictionType.FLOOD:
            raise ValueError(
                f"Unsupported prediction_type '{self.prediction_type}'. "
                "Only 'flood' is supported in this version."
            )
        return self

    def to_feature_dict(self) -> dict[str, Any]:
        """Convert request to the feature dict expected by the ML model."""
        return {
            "rainfall_mm": self.rainfall_mm,
            "river_level_m": self.river_level_m,
            "soil_moisture_pct": self.soil_moisture_pct,
            "temperature_c": self.temperature_c,
            "humidity_pct": self.humidity_pct,
            "previous_flood_events": self.previous_flood_events,
            "elevation_m": self.elevation_m,
            "population_density": self.population_density,
        }


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/predict",
    summary="Run a flood prediction",
    description="""
Submit environmental sensor readings to the flood prediction model
and receive a risk assessment.

### Prediction type
Currently only **`flood`** is supported.

### Required input features

| Feature | Type | Description |
|---|---|---|
| `rainfall_mm` | float ≥ 0 | Recent rainfall in millimetres |
| `river_level_m` | float ≥ 0 | River water level in metres |
| `soil_moisture_pct` | float 0–100 | Soil moisture percentage |
| `temperature_c` | float | Ambient temperature in Celsius |
| `humidity_pct` | float 0–100 | Relative humidity percentage |
| `previous_flood_events` | int ≥ 0 | Historical flood event count |
| `elevation_m` | float | Terrain elevation in metres |
| `population_density` | float ≥ 0 | People per square kilometre |

### Response fields

| Field | Type | Description |
|---|---|---|
| `prediction` | int | `1` = flood likely, `0` = flood unlikely |
| `confidence` | float | Model confidence in the prediction (0.0–1.0) |
| `risk_level` | str | `low` \\| `medium` \\| `high` \\| `critical` |
| `probability` | float | Raw flood probability (0.0–1.0) |
| `model` | str | Model identifier used for this prediction |

### Risk level thresholds
- `critical` — probability ≥ 0.75
- `high`     — probability ≥ 0.50
- `medium`   — probability ≥ 0.25
- `low`      — probability < 0.25

### Error codes
- **503** — model file not found on disk
- **422** — missing or invalid input features
- **500** — model inference failure

Requires: **Government** or **NGO** role.
    """,
)
async def predict(
    payload: Annotated[
        FloodPredictionRequest,
        Body(
            openapi_examples={
                "high_risk_scenario": {
                    "summary": "High-risk flood scenario",
                    "value": {
                        "prediction_type": "flood",
                        "rainfall_mm": 220.0,
                        "river_level_m": 7.5,
                        "soil_moisture_pct": 92.0,
                        "temperature_c": 28.5,
                        "humidity_pct": 95.0,
                        "previous_flood_events": 5,
                        "elevation_m": 3.0,
                        "population_density": 4200.0,
                    },
                },
                "low_risk_scenario": {
                    "summary": "Low-risk scenario",
                    "value": {
                        "prediction_type": "flood",
                        "rainfall_mm": 15.0,
                        "river_level_m": 1.2,
                        "soil_moisture_pct": 30.0,
                        "temperature_c": 35.0,
                        "humidity_pct": 45.0,
                        "previous_flood_events": 0,
                        "elevation_m": 85.0,
                        "population_density": 320.0,
                    },
                },
                "coastal_district": {
                    "summary": "Coastal district — moderate risk",
                    "value": {
                        "prediction_type": "flood",
                        "rainfall_mm": 95.0,
                        "river_level_m": 3.8,
                        "soil_moisture_pct": 65.0,
                        "temperature_c": 30.0,
                        "humidity_pct": 80.0,
                        "previous_flood_events": 2,
                        "elevation_m": 18.0,
                        "population_density": 1500.0,
                    },
                },
            }
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: _RequireGovOrNGO,
) -> Any:
    features = payload.to_feature_dict()
    result = prediction_service.run_flood_prediction(features=features)

    risk = result.get("risk_level", "unknown")
    pred = result.get("prediction", -1)
    verdict = "Flood likely" if pred == 1 else "Flood unlikely"

    return success_response(
        data=result,
        message=f"{verdict}. Risk level: {risk}.",
    )
