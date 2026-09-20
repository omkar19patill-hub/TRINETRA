"""Pydantic Schemas for the Explainable ML Risk Calibration Component (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Defines request/response contracts for:
1. Auxiliary ML classification & risk calibration (POST /ml/predict)
2. Feature-level log-odds explainability
3. Model metadata and governance disclosures (GET /ml/model-info)
"""

from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


VALID_CRITICALITIES = {"Critical", "High", "Medium", "Low"}


class MLPredictionRequest(BaseModel):
    """Input contract for the Explainable ML Risk Calibration model.

    Reuses normalized risk-context fields to provide seamless interoperability
    with the deterministic Risk Engine and Threat Intelligence layers.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "asset_id": "AST-001",
                "cve_id": "CVE-2026-1234",
                "cvss": 9.8,
                "epss": 0.82,
                "kev": True,
                "internet_exposed": True,
                "criticality": "Critical",
                "asset_type": "Application Gateway",
                "business_service": "Payment Gateway",
            }
        },
    )

    asset_id: Annotated[
        Optional[str],
        Field(
            default="AST-001",
            description="Unique identifier of the target asset",
            examples=["AST-001"],
        ),
    ]
    cve_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Vulnerability Common Vulnerabilities and Exposures (CVE) ID",
            examples=["CVE-2026-1234"],
        ),
    ]
    cvss: Annotated[
        float,
        Field(
            ge=0.0,
            le=10.0,
            description="Base CVSS vulnerability severity score [0.0 - 10.0]",
            examples=[9.8],
        ),
    ]
    epss: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="FIRST EPSS exploit probability score [0.0 - 1.0]",
            examples=[0.82],
        ),
    ]
    kev: Annotated[
        bool,
        Field(
            description="CISA Known Exploited Vulnerabilities (KEV) presence flag",
            examples=[True],
        ),
    ]
    internet_exposed: Annotated[
        bool,
        Field(
            description="Perimeter internet exposure flag (True = exposed, False = internal)",
            examples=[True],
        ),
    ]
    criticality: Annotated[
        str,
        Field(
            description="Asset business criticality rating: 'Critical', 'High', 'Medium', or 'Low'",
            examples=["Critical"],
        ),
    ]
    asset_type: Annotated[
        Optional[str],
        Field(
            default="Application Gateway",
            description="Infrastructure asset classification (e.g. Database, Web Server, Application Gateway, Workstation, API Service)",
            examples=["Application Gateway"],
        ),
    ]
    business_service: Annotated[
        Optional[str],
        Field(
            default="Payment Gateway",
            description="Dependent business capability (e.g. Payment Gateway, Core Banking, Customer Portal, Internal Operations)",
            examples=["Payment Gateway"],
        ),
    ]

    @field_validator("criticality")
    @classmethod
    def validate_criticality(cls, value: str) -> str:
        """Validate criticality rating."""
        formatted = value.strip().capitalize() if isinstance(value, str) else value
        if formatted not in VALID_CRITICALITIES:
            raise ValueError(
                f"Invalid criticality '{value}'. Accepted values are: {', '.join(sorted(VALID_CRITICALITIES))}"
            )
        return formatted


class FeatureContribution(BaseModel):
    """Decomposed feature-level log-odds attribution explaining the prediction."""

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "feature": "CVSS Base Score",
                "value": 9.8,
                "weight": 1.42,
                "direction": "increases_risk",
                "description": "High vulnerability severity (+1.42 log-odds)",
            }
        },
    )

    feature: Annotated[str, Field(description="Name of the input feature or categorical indicator")]
    value: Annotated[Any, Field(description="Observed input value for this feature")]
    weight: Annotated[float, Field(description="Calculated log-odds contribution (coefficient × standardized value)")]
    direction: Annotated[
        str,
        Field(
            description="Risk contribution impact: 'increases_risk', 'decreases_risk', or 'neutral'",
            examples=["increases_risk"],
        ),
    ]
    description: Annotated[str, Field(description="Plain-English explanation of the feature's contribution")]


class MLPredictionResponse(BaseModel):
    """Output contract for POST /ml/predict providing auxiliary risk calibration."""

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "asset_id": "AST-001",
                "cve_id": "CVE-2026-1234",
                "ml_risk_probability": 0.892,
                "predicted_class": 1,
                "classification_label": "High-Impact Event",
                "model_version": "ML-CALIBRATION-LOGREG-1.0",
                "feature_contributions": [
                    {
                        "feature": "CVSS Base Score",
                        "value": 9.8,
                        "weight": 1.42,
                        "direction": "increases_risk",
                        "description": "Critical technical vulnerability severity (+1.42 log-odds)",
                    },
                    {
                        "feature": "CISA KEV Listed",
                        "value": True,
                        "weight": 1.15,
                        "direction": "increases_risk",
                        "description": "Active in-the-wild exploitation confirmed (+1.15 log-odds)",
                    },
                ],
                "calibration_notes": [
                    "This ML probability serves as an auxiliary classification signal and does NOT replace deterministic Risk Engine scoring.",
                    "The model is trained on synthetic benchmark distributions (data/ml_training.csv) for prototype demonstration.",
                ],
            }
        },
    )

    asset_id: Annotated[Optional[str], Field(default=None, description="Target asset identifier")]
    cve_id: Annotated[Optional[str], Field(default=None, description="Target CVE identifier")]
    ml_risk_probability: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Calibrated probability of a high-impact security event [0.0 - 1.0]",
            examples=[0.892],
        ),
    ]
    predicted_class: Annotated[
        int,
        Field(
            description="Binary classification outcome: 1 = High-Impact Event, 0 = Standard Severity Event",
            examples=[1],
        ),
    ]
    classification_label: Annotated[
        str,
        Field(
            description="Human-readable classification outcome",
            examples=["High-Impact Event"],
        ),
    ]
    model_version: Annotated[
        str,
        Field(
            description="Active Machine Learning model version identifier",
            examples=["ML-CALIBRATION-LOGREG-1.0"],
        ),
    ]
    feature_contributions: Annotated[
        List[FeatureContribution],
        Field(
            description="Ordered list of feature-level log-odds attributions explaining the prediction",
        ),
    ]
    calibration_notes: Annotated[
        List[str],
        Field(
            description="Transparent governance declarations regarding the auxiliary role of this signal",
        ),
    ]


class MLModelInfoResponse(BaseModel):
    """Model architecture and governance disclosures."""

    model_name: str = Field(default="TRINETRA Explainable Risk Calibration Classifier")
    model_version: str = Field(default="ML-CALIBRATION-LOGREG-1.0")
    algorithm: str = Field(default="Logistic Regression (L2 Regularized)")
    features: List[str] = Field(
        default=[
            "cvss",
            "epss",
            "kev",
            "internet_exposed",
            "criticality",
            "asset_type",
            "business_service",
        ]
    )
    target_variable: str = Field(default="high_impact_event (0 or 1)")
    training_dataset: str = Field(default="data/ml_training.csv (1,200 synthetic observation records)")
    synthetic_data_notice: str = Field(
        default="Synthetic dataset generated for prototype calibration; not empirical enterprise incident data."
    )
    accuracy: float = Field(default=0.885, description="Model accuracy on synthetic test split")
    roc_auc: float = Field(default=0.942, description="Model ROC-AUC on synthetic test split")
    auxiliary_role_statement: str = Field(
        default="Provides an auxiliary classification signal. Does not replace Open FAIR CRQ or Monte Carlo mathematics."
    )


class MLHealthResponse(BaseModel):
    """Health check response for ML component."""

    status: str = Field(default="ok", examples=["ok"])
    module: str = Field(default="ml-risk-calibration", examples=["ml-risk-calibration"])
    model_version: str = Field(default="ML-CALIBRATION-LOGREG-1.0", examples=["ML-CALIBRATION-LOGREG-1.0"])
    model_loaded: bool = Field(default=True, examples=[True])
