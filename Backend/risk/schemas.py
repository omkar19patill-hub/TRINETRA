"""Pydantic Schemas for the Risk Engine

TRINETRA - SIH 2026

Defines request/response contracts, data validation rules, and explainable
calculation structures.
"""

from enum import Enum
from typing import Annotated, List
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

