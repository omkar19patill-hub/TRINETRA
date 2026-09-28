"""TRINETRA Cyber Risk Engine Module

AI-Powered Continuous Cyber Risk Quantification & Investment Optimization Platform
SIH 2026

Deterministic and explainable risk quantification module.
"""

from .constants import (
    MODEL_VERSION,
    MODEL_TYPE,
    CVSS_WEIGHT,
    EPSS_WEIGHT,
    KEV_WEIGHT,
    EXPOSURE_WEIGHT,
    CRITICALITY_IMPACT,
)
from .schemas import (
    RiskCalculationRequest,
    RiskCalculationResponse,
    RiskInput,
    RiskResult,
    CalculationBreakdown,
    ModelInfo,
    CriticalityEnum,
    HealthResponse,
    AssessmentResultItem,
    AssessmentBatchCreate,
    RiskSnapshotResponse,
    AssessmentBatchResponse,
    RiskChangeResponse,
    RiskAppetiteStatus,
    RiskAppetiteRequest,
    RiskIntelligenceResponse,
)

from .scoring import (
    normalize_cvss,
    calculate_likelihood,
    calculate_impact,
    calculate_risk_score,
    get_risk_level,
)
from .drivers import generate_risk_drivers
from .engine import calculate_risk
from .change_detector import compute_risk_change, detect_latest_risk_change
from .risk_intelligence import calculate_risk_intelligence, get_risk_intelligence
from .storage import (

    AssessmentStorage,
    get_assessment_storage,
    set_assessment_storage,
    init_assessment_storage,
)


__all__ = [
    "MODEL_VERSION",
    "MODEL_TYPE",
    "CVSS_WEIGHT",
    "EPSS_WEIGHT",
    "KEV_WEIGHT",
    "EXPOSURE_WEIGHT",
    "CRITICALITY_IMPACT",
    "RiskCalculationRequest",
    "RiskCalculationResponse",
    "RiskInput",
    "RiskResult",
    "CalculationBreakdown",
    "ModelInfo",
    "CriticalityEnum",
    "HealthResponse",
    "AssessmentResultItem",
    "AssessmentBatchCreate",
    "RiskSnapshotResponse",
    "AssessmentBatchResponse",
    "RiskChangeResponse",
    "RiskAppetiteStatus",
    "RiskAppetiteRequest",
    "RiskIntelligenceResponse",
    "AssessmentStorage",
    "get_assessment_storage",
    "set_assessment_storage",
    "init_assessment_storage",
    "normalize_cvss",
    "calculate_likelihood",
    "calculate_impact",
    "calculate_risk_score",
    "get_risk_level",
    "generate_risk_drivers",
    "calculate_risk",
    "compute_risk_change",
    "detect_latest_risk_change",
    "calculate_risk_intelligence",
    "get_risk_intelligence",
]




