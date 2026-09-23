"""Data Models and Pydantic Schemas for Security Controls Catalog (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Defines structured data contracts for:
1. Security Control Specification with Factor Effects
2. Control Assessment Request and Response Contracts
3. Catalog Filtering and Inspection Schemas
"""

from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskReductionEffect(BaseModel):
    """Specification of how a cybersecurity control alters underlying risk and financial factors.
    
    Rather than subtracting arbitrary risk percentages, each control deterministically
    modifies concrete vulnerability, exploitability, and impact metrics.
    """

    model_config = ConfigDict(extra="ignore")

    epss_multiplier: Annotated[
        float,
        Field(
            default=1.0,
            ge=0.0,
            le=1.0,
            description="Multiplier applied to EPSS score (e.g., 0.50 cuts exploitation probability by half)",
        ),
    ]
    likelihood_mitigation_factor: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            le=1.0,
            description="Proportional mitigation applied to exploit likelihood (0.0 to 1.0)",
        ),
    ]
    cvss_reduction: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            le=10.0,
            description="Direct reduction in effective CVSS score (e.g., 3.5 for virtual patching)",
        ),
    ]
    exposure_mitigation: Annotated[
        bool,
        Field(
            default=False,
            description="True if the control shields or neutralizes external internet exposure (e.g. WAF, ZTNA)",
        ),
    ]
    kev_neutralized: Annotated[
        bool,
        Field(
            default=False,
            description="True if the control neutralizes active CISA KEV exploitation techniques (e.g. Patching)",
        ),
    ]
    downtime_reduction_pct: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            le=1.0,
            description="Percentage reduction in operational downtime hours (e.g., 0.60 for Backups)",
        ),
    ]
    recovery_cost_reduction_pct: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            le=1.0,
            description="Percentage reduction in recovery and rebuild costs (e.g., 0.50)",
        ),
    ]
    incident_response_reduction_pct: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            le=1.0,
            description="Percentage reduction in incident response & forensics costs (e.g., 0.40 for EDR/SIEM)",
        ),
    ]
    regulatory_reduction_pct: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            le=1.0,
            description="Percentage reduction in regulatory fines & penalties (e.g., 0.70 for Data Encryption)",
        ),
    ]
    customer_impact_reduction_pct: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            le=1.0,
            description="Percentage reduction in customer compensation and SLA damages (e.g., 0.60 for Data Encryption)",
        ),
    ]


class SecurityControl(BaseModel):
    """Specification of an enterprise security control candidate."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "control_id": "CTRL-MFA",
                "control_name": "Phishing-Resistant MFA",
                "description": "FIDO2 hardware token multi-factor authentication across all identity providers.",
                "category": "Identity & Access",
                "implementation_cost": 350000.0,
                "annual_cost": 75000.0,
                "risk_reduction_effect": {
                    "epss_multiplier": 0.50,
                    "likelihood_mitigation_factor": 0.35,
                },
                "applicable_asset_types": ["web_application", "api_gateway", "workstation", "cloud_server", "all"],
                "required_dependencies": [],
                "implementation_time": 14,
                "confidence": 0.95,
            }
        },
    )

    control_id: Annotated[
        str,
        Field(
            min_length=1,
            description="Unique identifier of the control (e.g. CTRL-MFA, CTRL-EDR)",
        ),
    ]
    control_name: Annotated[
        str,
        Field(
            min_length=1,
            description="Human-readable standard name of the security control",
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="Technical and operational description of the control",
        ),
    ]
    category: Annotated[
        str,
        Field(
            description="Control classification (e.g. Identity & Access, Endpoint Security, Network Security)",
        ),
    ]
    implementation_cost: Annotated[
        float,
        Field(
            ge=0.0,
            description="One-time monetary cost to acquire, architect, and deploy the control",
        ),
    ]
    annual_cost: Annotated[
        float,
        Field(
            ge=0.0,
            description="Annual recurring operational, licensing, and maintenance expenditure",
        ),
    ]
    risk_reduction_effect: Annotated[
        RiskReductionEffect,
        Field(
            default_factory=RiskReductionEffect,
            description="Deterministic factor effect on vulnerability and financial impact metrics",
        ),
    ]
    applicable_asset_types: Annotated[
        List[str],
        Field(
            default_factory=lambda: ["all"],
            description="Asset categories where this control can be deployed",
        ),
    ]
    required_dependencies: Annotated[
        List[str],
        Field(
            default_factory=list,
            description="List of control_ids required as prerequisites before this control can be activated",
        ),
    ]
    implementation_time: Annotated[
        int,
        Field(
            ge=0,
            description="Estimated implementation elapsed duration in calendar days",
        ),
    ]
    confidence: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=0.90,
            description="Statistical confidence score in modeled control efficacy (0.0 - 1.0)",
        ),
    ]


class ControlCatalogResponse(BaseModel):
    """API response contract returning the security control catalog."""

    model_config = ConfigDict(extra="ignore")

    total_controls: int = Field(description="Total count of available controls")
    categories: List[str] = Field(description="Unique control categories present in catalog")
    controls: List[SecurityControl] = Field(description="List of security control specifications")
    version: str = Field(default="CTRL-1.0", description="Control catalog schema version")


class ControlAssessmentItem(BaseModel):
    """Individual control assessment result."""

    control_id: str
    control_name: str
    is_applicable: bool
    dependencies_satisfied: bool
    missing_dependencies: List[str]
    implementation_cost: float
    annual_cost: float
    estimated_risk_reduction: float
    estimated_eal_avoided: float
    efficiency_ratio: float
    recommendation: str


class ControlAssessRequest(BaseModel):
    """Payload to assess one or more controls against an asset context."""

    model_config = ConfigDict(extra="ignore")

    control_ids: Optional[List[str]] = Field(
        default=None,
        description="List of control_ids to evaluate. If omitted, evaluates all catalog controls.",
    )
    asset_id: Optional[str] = Field(default="AST-001", description="Identifier of the target asset")
    asset_type: Optional[str] = Field(default="web_application", description="Type of the asset")
    existing_controls: Optional[List[str]] = Field(
        default_factory=list,
        description="Controls already implemented on the asset to satisfy prerequisites",
    )
    cvss: Optional[float] = Field(default=9.8, ge=0.0, le=10.0)
    epss: Optional[float] = Field(default=0.82, ge=0.0, le=1.0)
    kev: Optional[bool] = Field(default=True)
    internet_exposed: Optional[bool] = Field(default=True)
    criticality: Optional[str] = Field(default="Critical")
    revenue_loss_per_hour: Optional[float] = Field(default=250000.0, ge=0.0)
    downtime_hours: Optional[float] = Field(default=8.0, ge=0.0)
    incident_response_cost: Optional[float] = Field(default=150000.0, ge=0.0)
    recovery_cost: Optional[float] = Field(default=200000.0, ge=0.0)
    regulatory_legal_cost: Optional[float] = Field(default=500000.0, ge=0.0)
    customer_business_impact: Optional[float] = Field(default=300000.0, ge=0.0)


class ControlAssessResponse(BaseModel):
    """API response contract for control assessment endpoint."""

    model_config = ConfigDict(extra="ignore")

    asset_id: str
    asset_type: str
    baseline_risk_score: float
    baseline_eal: float
    assessments: List[ControlAssessmentItem]
    assessed_count: int
    version: str = "CTRL-1.0"


class DependencyItem(BaseModel):
    """Prerequisite dependency status within a control resolution bundle."""

    model_config = ConfigDict(extra="ignore")

    control_id: str = Field(description="Identifier of required dependency control")
    status: str = Field(description="Dependency status: 'included', 'unavailable', or 'already_selected'")
    reason: str = Field(description="Reason for dependency status")


class ControlDependencyResolution(BaseModel):
    """Detailed dependency resolution record for an evaluated control matching exact problem specification."""

    model_config = ConfigDict(extra="ignore")

    control_id: str = Field(description="Identifier of evaluated control")
    status: str = Field(description="Resolution status: 'selected' or 'rejected'")
    dependencies: List[DependencyItem] = Field(
        default_factory=list,
        description="List of resolved prerequisite dependencies",
    )
    bundle_cost: float = Field(
        ge=0.0,
        description="Total bundled implementation cost (primary control + newly included dependencies)",
    )
    bundle_annual_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Total annual recurring operational cost for the bundle",
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Explanation if control or bundle was rejected",
    )


class ControlDependencyResolveRequest(BaseModel):
    """Request payload to validate and resolve dependencies for requested controls."""

    model_config = ConfigDict(extra="ignore")

    requested_control_ids: List[str] = Field(
        description="List of control IDs to evaluate and resolve",
    )
    asset_id: Optional[str] = Field(default="AST-001", description="Identifier of the target asset")
    asset_type: Optional[str] = Field(default="web_application", description="Type of the asset")
    budget_limit: float = Field(default=1800000.0, description="Available capital investment budget")
    existing_controls: Optional[List[str]] = Field(
        default_factory=list,
        description="Controls already implemented in the environment",
    )
    allow_override: bool = Field(
        default=False,
        description="Allow override of asset applicability rules if explicitly authorized",
    )

