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
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.core.permissions import require_role
from app.database.session import get_db
from app.models.enums import RoleEnum
from app.models.user import User
from app.services import prediction_service, severity_prediction_service
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
# Priority / relief-units prediction — trained on the hackathon-provided
# disaster_relief_resource_allocation.csv dataset (see ml/train_priority_model.py)
# ---------------------------------------------------------------------------

class PriorityDisasterType(str, Enum):
    FLOOD = "Flood"
    CYCLONE = "Cyclone"
    EARTHQUAKE = "Earthquake"
    DROUGHT = "Drought"
    WILDFIRE = "Wildfire"
    LANDSLIDE = "Landslide"
    EPIDEMIC_OUTBREAK = "Epidemic Outbreak"
    TSUNAMI = "Tsunami"


class PrioritySeverityLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class AccessibilityStatus(str, Enum):
    ACCESSIBLE = "Accessible"
    PARTIALLY_ACCESSIBLE = "Partially Accessible"
    INACCESSIBLE = "Inaccessible"


class CommunicationStatus(str, Enum):
    FULL = "Full"
    PARTIAL = "Partial"
    DOWN = "Down"


class PowerStatus(str, Enum):
    AVAILABLE = "Available"
    PARTIAL = "Partial"
    DOWN = "Down"


class PriorityPredictionRequest(BaseModel):
    """
    Input payload for the resource-allocation priority prediction endpoint.

    Trained on 200k real incident records from the hackathon-provided
    dataset — predicts both allocation_priority (classification) and
    recommended_relief_units (regression) from the same inputs.
    """

    population_affected: int = Field(..., ge=0, examples=[8309])
    households_affected: int = Field(..., ge=0, examples=[1729])
    infrastructure_damage_score: float = Field(..., ge=0.0, le=100.0, examples=[49.5])
    nearest_relief_center_distance_km: float = Field(..., ge=0.0, examples=[14.25])
    available_volunteers: int = Field(..., ge=0, examples=[27])
    medical_teams_available: int = Field(..., ge=0, examples=[2])
    food_stock_kg: float = Field(..., ge=0.0, examples=[210.0])
    water_stock_liters: float = Field(..., ge=0.0, examples=[1725.0])
    shelter_capacity: float = Field(..., ge=0.0, examples=[292.0])
    funding_available_usd: float = Field(..., ge=0.0, examples=[46534.98])
    vulnerability_index: float = Field(..., ge=0.0, le=1.0, examples=[0.277])
    ngo_present: bool = Field(..., examples=[True])
    government_response_active: bool = Field(..., examples=[True])
    disaster_type: PriorityDisasterType = Field(..., examples=["Flood"])
    severity_level: PrioritySeverityLevel = Field(..., examples=["High"])
    accessibility_status: AccessibilityStatus = Field(..., examples=["Accessible"])
    communication_status: CommunicationStatus = Field(..., examples=["Full"])
    power_status: PowerStatus = Field(..., examples=["Partial"])

    def to_feature_dict(self) -> dict[str, Any]:
        return {
            "population_affected": self.population_affected,
            "households_affected": self.households_affected,
            "infrastructure_damage_score": self.infrastructure_damage_score,
            "nearest_relief_center_distance_km": self.nearest_relief_center_distance_km,
            "available_volunteers": self.available_volunteers,
            "medical_teams_available": self.medical_teams_available,
            "food_stock_kg": self.food_stock_kg,
            "water_stock_liters": self.water_stock_liters,
            "shelter_capacity": self.shelter_capacity,
            "funding_available_usd": self.funding_available_usd,
            "vulnerability_index": self.vulnerability_index,
            "ngo_present": self.ngo_present,
            "government_response_active": self.government_response_active,
            "disaster_type": self.disaster_type.value,
            "severity_level": self.severity_level.value,
            "accessibility_status": self.accessibility_status.value,
            "communication_status": self.communication_status.value,
            "power_status": self.power_status.value,
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


@router.post(
    "/predict-priority",
    summary="Predict resource allocation priority and recommended relief units",
    description="""
Submit incident details and receive an AI-predicted **allocation priority**
(Low/Medium/High/Critical) and **recommended relief units** — trained on
200,000 real incident records from the hackathon-provided
`disaster_relief_resource_allocation.csv` dataset.

Two models run together: a RandomForestClassifier for priority and a
RandomForestRegressor for relief units, both full scikit-learn pipelines
(imputation + encoding + estimator) trained by `ml/train_priority_model.py`.

### Response fields

| Field | Type | Description |
|---|---|---|
| `allocation_priority` | str | `Low` \\| `Medium` \\| `High` \\| `Critical` |
| `confidence` | float | Probability of the predicted priority class |
| `class_probabilities` | dict | Probability for every priority class |
| `recommended_relief_units` | int | Predicted relief units needed |

### Error codes
- **503** — model files not found on disk (run the training script first)
- **422** — missing or invalid input features
- **500** — model inference failure

Requires: **Government** or **NGO** role.
    """,
)
async def predict_priority(
    payload: Annotated[
        PriorityPredictionRequest,
        Body(
            openapi_examples={
                "high_priority_flood": {
                    "summary": "Under-resourced flood, poor accessibility",
                    "value": {
                        "population_affected": 8309,
                        "households_affected": 1729,
                        "infrastructure_damage_score": 49.5,
                        "nearest_relief_center_distance_km": 14.25,
                        "available_volunteers": 27,
                        "medical_teams_available": 2,
                        "food_stock_kg": 210.0,
                        "water_stock_liters": 1725.0,
                        "shelter_capacity": 292.0,
                        "funding_available_usd": 46534.98,
                        "vulnerability_index": 0.277,
                        "ngo_present": True,
                        "government_response_active": True,
                        "disaster_type": "Flood",
                        "severity_level": "High",
                        "accessibility_status": "Accessible",
                        "communication_status": "Full",
                        "power_status": "Partial",
                    },
                },
                "critical_earthquake": {
                    "summary": "Critical earthquake, inaccessible, comms down",
                    "value": {
                        "population_affected": 16386,
                        "households_affected": 4164,
                        "infrastructure_damage_score": 92.0,
                        "nearest_relief_center_distance_km": 48.0,
                        "available_volunteers": 8,
                        "medical_teams_available": 1,
                        "food_stock_kg": 150.0,
                        "water_stock_liters": 200.0,
                        "shelter_capacity": 90.0,
                        "funding_available_usd": 4000.0,
                        "vulnerability_index": 0.35,
                        "ngo_present": False,
                        "government_response_active": False,
                        "disaster_type": "Earthquake",
                        "severity_level": "Critical",
                        "accessibility_status": "Inaccessible",
                        "communication_status": "Down",
                        "power_status": "Down",
                    },
                },
            }
        ),
    ],
    current_user: _RequireGovOrNGO,
) -> Any:
    features = payload.to_feature_dict()
    result = severity_prediction_service.run_priority_prediction(features=features)

    return success_response(
        data=result,
        message=(
            f"Predicted priority: {result.get('allocation_priority')} "
            f"({result.get('confidence', 0) * 100:.0f}% confidence). "
            f"Recommended relief units: {result.get('recommended_relief_units')}."
        ),
    )
