"""
app/api/v1/prediction.py

AI Prediction router — framework skeleton.

Exposes ML model inference endpoints.  The underlying prediction logic
lives in ml/predict.py and is accessed via the prediction service.

Prefix  : /api/v1/prediction
Tags    : AI Prediction
"""

from fastapi import APIRouter

from app.utils.constants import API_V1_TAG_PREDICTION

router = APIRouter(
    prefix="/prediction",
    tags=[API_V1_TAG_PREDICTION],
)

# ---------------------------------------------------------------------------
# Endpoint stubs — implementation deferred to future phase
# ---------------------------------------------------------------------------
# POST /prediction/disaster-risk      → Predict disaster risk for a given region
# POST /prediction/resource-needs     → Estimate resource requirements
# POST /prediction/affected-population → Estimate affected population count
# GET  /prediction/model-info         → Retrieve loaded model metadata
# POST /prediction/batch              → Run batch predictions on multiple inputs
