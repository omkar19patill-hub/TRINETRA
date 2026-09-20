"""FastAPI Router for the Explainable ML Risk Calibration Component

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Explainable ML Risk Calibration Endpoints
"""

from fastapi import APIRouter, status
from .schemas import (
    MLHealthResponse,
    MLModelInfoResponse,
    MLPredictionRequest,
    MLPredictionResponse,
)
from .model import get_model


router = APIRouter(prefix="/ml", tags=["ML Risk Calibration"])


@router.post(
    "/predict",
    response_model=MLPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Auxiliary High-Impact Risk Probability with Feature Explanations",
    description="""
Evaluates an explainable Logistic Regression classifier to produce an auxiliary
risk-calibration classification signal (`high_impact_event: 0/1`) and probability score.

**Key Design & Governance Guarantees:**
1. **Auxiliary Signal:** Does **NOT** replace or override the deterministic Cyber Risk Engine or Open FAIR CRQ.
2. **Zero Financial Loss Prediction:** Classifies risk event severity, not currency numbers.
3. **100% Explainable:** Decomposes the classification logit into exact feature-level log-odds contributions.
4. **Synthetic Data Transparency:** Calibrated on documented synthetic benchmark observations (`data/ml_training.csv`).
""",
)
def predict_risk_endpoint(request: MLPredictionRequest) -> MLPredictionResponse:
    """Predict auxiliary risk probability and return decomposed feature log-odds attributions."""
    model = get_model()
    return model.predict(request)


@router.get(
    "/model-info",
    response_model=MLModelInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Machine Learning Model Architecture & Performance Disclosures",
    description="Returns metadata about model architecture, training dataset, accuracy, ROC-AUC, and governance guidelines.",
)
def model_info_endpoint() -> MLModelInfoResponse:
    """Return model architecture and governance disclosures."""
    model = get_model()
    return model.get_info()


@router.get(
    "/health",
    response_model=MLHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check for the ML Risk Calibration module",
    description="Returns operational status, model loaded state, and active ML model version.",
)
def health_check() -> MLHealthResponse:
    """Health check endpoint for ML module monitoring."""
    model = get_model()
    return model.health()
