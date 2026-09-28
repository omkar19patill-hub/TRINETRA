"""Pydantic Schemas for the Risk Engine

TRINETRA - SIH 2026

Defines request/response contracts, data validation rules, and explainable
calculation structures.
"""

from enum import Enum
from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CriticalityEnum(str, Enum):
    """Business criticality tiers for enterprise assets."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RiskCalculationRequest(BaseModel):
    """Input contract for the Risk Engine calculation.

    Takes vulnerability severity metrics (CVSS, EPSS, KEV) paired with
    asset operational context (internet exposure, business criticality).
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
            }
        },
    )

    asset_id: Annotated[
        str,
        Field(
            min_length=1,
            description="Unique identifier of the target asset (e.g., AST-001)",
            examples=["AST-001"],
        ),
    ]
    cve_id: Annotated[
        str,
        Field(
            min_length=1,
            description="Vulnerability Common Vulnerabilities and Exposures ID (e.g., CVE-2026-1234)",
            examples=["CVE-2026-1234"],
        ),
    ]
    cvss: Annotated[
        float,
        Field(
            ge=0.0,
            le=10.0,
            description="CVSS base score (0.0 to 10.0)",
            examples=[9.8],
        ),
    ]
    epss: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Exploit Prediction Scoring System probability (0.0 to 1.0)",
            examples=[0.82],
        ),
    ]
    kev: Annotated[
        bool,
        Field(
            description="Flag indicating if the vulnerability is listed in the CISA KEV catalog",
            examples=[True],
        ),
    ]
    internet_exposed: Annotated[
        bool,
        Field(
            description="Flag indicating if the asset has direct internet routability/exposure",
            examples=[True],
        ),
    ]
    criticality: Annotated[
        CriticalityEnum,
        Field(
            description="Asset business criticality rating: 'Critical', 'High', 'Medium', or 'Low'",
            examples=["Critical"],
        ),
    ]


class CalculationBreakdown(BaseModel):
    """Transparent calculation breakdown for SIH explainability and auditing."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cvss_normalized": 0.98,
                "epss": 0.82,
                "kev_signal": 1,
                "exposure_signal": 1,
                "cvss_contribution": 0.245,
                "epss_contribution": 0.328,
                "kev_contribution": 0.20,
                "exposure_contribution": 0.15,
            }
        }
    )

    cvss_normalized: float = Field(
        description="CVSS score scaled to [0.0 - 1.0] (CVSS / 10.0)"
    )
    epss: float = Field(
        description="Raw EPSS exploitation probability score [0.0 - 1.0]"
    )
    kev_signal: int = Field(
        description="Binary signal for CISA KEV catalog presence (1 if True, 0 if False)"
    )
    exposure_signal: int = Field(
        description="Binary signal for internet exposure (1 if True, 0 if False)"
    )
    cvss_contribution: float = Field(
        description="Likelihood contribution from normalized CVSS (weight * cvss_normalized)"
    )
    epss_contribution: float = Field(
        description="Likelihood contribution from EPSS (weight * epss)"
    )
    kev_contribution: float = Field(
        description="Likelihood contribution from KEV presence (weight * kev_signal)"
    )
    exposure_contribution: float = Field(
        description="Likelihood contribution from Internet exposure (weight * exposure_signal)"
    )


class ModelInfo(BaseModel):
    """Model metadata and governance specification."""
    version: str = Field(
        description="Risk scoring model version identifier",
        examples=["risk-model-v1"],
    )
    type: str = Field(
        description="Type of computation (deterministic rule-based)",
        examples=["deterministic"],
    )


class RiskCalculationResponse(BaseModel):
    """Complete output contract of the Risk Engine."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "AST-001",
                "cve_id": "CVE-2026-1234",
                "likelihood": 0.895,
                "impact": 1.0,
                "risk_score": 89.5,
                "risk_level": "CRITICAL",
                "risk_drivers": [
                    "Critical CVSS",
                    "High exploitation probability",
                    "Known exploited vulnerability",
                    "Internet exposed asset",
                    "Critical business asset",
                ],
                "calculation": {
                    "cvss_normalized": 0.98,
                    "epss": 0.82,
                    "kev_signal": 1,
                    "exposure_signal": 1,
                    "cvss_contribution": 0.245,
                    "epss_contribution": 0.328,
                    "kev_contribution": 0.20,
                    "exposure_contribution": 0.15,
                },
                "model": {
                    "version": "risk-model-v1",
                    "type": "deterministic",
                },
            }
        }
    )

    asset_id: str = Field(description="Unique asset identifier")
    cve_id: str = Field(description="Vulnerability CVE identifier")
    likelihood: float = Field(
        description="Calculated composite likelihood of exploitation [0.0 - 1.0]"
    )
    impact: float = Field(
        description="Business impact multiplier based on asset criticality [0.0 - 1.0]"
    )
    risk_score: float = Field(
        description="Final deterministic risk score [0.0 - 100.0] = Likelihood * Impact * 100"
    )
    risk_level: str = Field(
        description="Categorical risk tier: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'"
    )
    risk_drivers: List[str] = Field(
        description="Qualitative explainability reasons indicating why the risk score reached this level"
    )
    calculation: CalculationBreakdown = Field(
        description="Step-by-step mathematical breakdown for auditability"
    )
    model: ModelInfo = Field(
        description="Model version and calculation type metadata"
    )


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="ok", examples=["ok"])
    module: str = Field(default="risk-engine", examples=["risk-engine"])
    model_version: str = Field(default="risk-model-v1", examples=["risk-model-v1"])


# Cross-module compatibility aliases
RiskInput = RiskCalculationRequest
RiskResult = RiskCalculationResponse


class AssessmentResultItem(BaseModel):
    """Individual asset assessment result within a batch."""
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    asset_id: str = Field(description="Unique asset identifier")
    asset_name: Optional[str] = Field(default=None, description="Human readable asset name")
    cve_id: Optional[str] = Field(default=None, description="Primary CVE evaluated")
    criticality: Optional[str] = Field(default=None, description="Business criticality tier")
    risk_score: float = Field(ge=0.0, le=100.0, description="Calculated deterministic risk score")
    financial_exposure: float = Field(ge=0.0, description="Calculated expected annual loss (EAL) in INR")
    assessment_data: dict[str, Any] = Field(default_factory=dict, description="Full serializable payload of risk & financial computation")


class AssessmentBatchCreate(BaseModel):
    """Input contract for persisting an assessment batch from Bulk Assessment."""
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    batch_id: Optional[str] = Field(default=None, description="Optional custom batch ID")
    source: str = Field(default="bulk_assessment_csv", description="Data source identifier (e.g. filename or channel)")
    total_rows: int = Field(ge=0, description="Total rows parsed in batch")
    successful_rows: int = Field(ge=0, description="Successfully processed rows")
    failed_rows: int = Field(default=0, ge=0, description="Failed rows in batch")
    status: str = Field(default="COMPLETED", description="Batch execution status")
    results: List[AssessmentResultItem] = Field(default_factory=list, description="List of successful asset assessments")
    risk_appetite: Optional[float] = Field(default=None, description="Optional organizational risk appetite threshold")


class RiskSnapshotResponse(BaseModel):
    """Immutable portfolio risk snapshot computed for an assessment batch."""
    model_config = ConfigDict(
        extra="forbid",
    )

    id: str = Field(description="Unique snapshot identifier")
    batch_id: Optional[str] = Field(default=None, description="Associated batch identifier")
    timestamp: str = Field(description="ISO timestamp of snapshot capture")
    total_exposure: float = Field(description="Aggregate Expected Annual Loss (EAL) across assessed assets")
    average_risk: float = Field(description="Mean deterministic risk score [0 - 100]")
    critical_assets: int = Field(description="Number of assets classified as Critical risk")
    high_risk_assets: int = Field(description="Number of assets classified as High risk")
    risk_appetite: Optional[float] = Field(default=None, description="Configured risk appetite threshold at time of snapshot")
    created_at: str = Field(description="Snapshot creation timestamp")


class AssessmentBatchResponse(BaseModel):
    """Output contract returned upon successfully persisting an assessment batch."""
    model_config = ConfigDict(
        extra="forbid",
    )

    batch_id: str = Field(description="Persisted batch identifier")
    created_at: str = Field(description="Batch creation timestamp")
    source: str = Field(description="Source identifier")
    total_rows: int = Field(description="Total rows in batch")
    successful_rows: int = Field(description="Successful rows")
    failed_rows: int = Field(description="Failed rows")
    status: str = Field(description="Batch status")
    snapshot: RiskSnapshotResponse = Field(description="Computed portfolio risk snapshot")



