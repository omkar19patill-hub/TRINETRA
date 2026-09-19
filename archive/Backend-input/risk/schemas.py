"""Pydantic Schemas for Cyber Risk Input and Result

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026

Person 1: Input validation schemas and response contracts.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


VALID_CRITICALITIES = {"Critical", "High", "Medium", "Low"}


class RiskInput(BaseModel):
    """Input payload for cyber risk assessment.

    Encapsulates vulnerability intelligence (CVSS, EPSS, KEV) paired with
    asset operational and business context (exposure, criticality).
    """

    asset_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the target asset",
        examples=["AST-001"],
    )
    cve_id: str = Field(
        ...,
        min_length=1,
        description="Common Vulnerabilities and Exposures (CVE) identifier",
        examples=["CVE-001"],
    )
    cvss: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="CVSS base score (between 0.0 and 10.0)",
        examples=[9.8],
    )
    epss: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="EPSS exploitation probability score (between 0.0 and 1.0)",
        examples=[0.82],
    )
    kev: bool = Field(
        ...,
        description="Indicates if the CVE is in the CISA Known Exploited Vulnerabilities catalog",
        examples=[True],
    )
    internet_exposed: bool = Field(
        ...,
        description="Indicates if the asset has direct internet connectivity/exposure",
        examples=[True],
    )
    criticality: str = Field(
        ...,
        description="Business criticality tier: 'Critical', 'High', 'Medium', or 'Low'",
        examples=["Critical"],
    )

    @field_validator("criticality")
    @classmethod
    def validate_criticality(cls, value: str) -> str:
        """Validate that criticality is strictly one of the accepted MVP values."""
        if value not in VALID_CRITICALITIES:
            raise ValueError(
                f"Invalid criticality '{value}'. Accepted values are: {', '.join(sorted(VALID_CRITICALITIES))}"
            )
        return value


class RiskResult(BaseModel):
    """Response schema for cyber risk calculation results.

    Contains quantified risk metrics, categorical risk level, and explainable drivers.
    For now, these fields are populated by a placeholder service until Person 2
    connects the risk calculation engine.
    """

    asset_id: str = Field(
        ...,
        description="Unique identifier of the evaluated asset",
        examples=["AST-001"],
    )
    cve_id: str = Field(
        ...,
        description="Evaluated Common Vulnerabilities and Exposures (CVE) identifier",
        examples=["CVE-001"],
    )
    likelihood: Optional[float] = Field(
        default=None,
        description="Calculated composite likelihood of exploitation (0.0 to 1.0)",
        examples=[None],
    )
    impact: Optional[float] = Field(
        default=None,
        description="Calculated business impact multiplier (0.0 to 1.0)",
        examples=[None],
    )
    risk_score: Optional[float] = Field(
        default=None,
        description="Calculated risk score (0.0 to 100.0)",
        examples=[None],
    )
    risk_level: Optional[str] = Field(
        default=None,
        description="Categorical risk tier (e.g. Critical, High, Medium, Low)",
        examples=[None],
    )
    risk_drivers: List[str] = Field(
        default_factory=list,
        description="List of primary factors contributing to the risk score",
        examples=[[]],
    )
