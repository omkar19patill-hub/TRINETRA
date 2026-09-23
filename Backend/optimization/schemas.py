"""Pydantic Schemas for Cybersecurity Investment Optimization

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Defines structured data contracts for:
1. Deterministic Fixed-Budget Optimization Run Requests & Unified Responses
2. Before-and-After Quantitative Portfolio Impact Comparisons
"""

from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from controls.models import ControlDependencyResolution, SecurityControl


OPTIMIZATION_MODEL_VERSION = "OPT-DET-1.0"



class OptimizationRunRequest(BaseModel):
    """Input payload to trigger deterministic cybersecurity investment portfolio optimization."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    budget_limit: Annotated[
        float,
        Field(
            ge=0.0,
            description="Total capital investment budget ceiling (currency: INR / configured currency)",
            examples=[1800000.0],
        ),
    ]
    asset_id: Annotated[
        Optional[str],
        Field(
            default="AST-001",
            description="Identifier of target asset under evaluation",
            examples=["AST-001"],
        ),
    ]
    optimization_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Optional custom identifier for the optimization run",
        ),
    ] = None
    asset_type: Annotated[
        Optional[str],
        Field(
            default="web_application",
            description="Asset archetype category (e.g. web_application, api_gateway, database, workstation, cloud_server)",
            examples=["web_application"],
        ),
    ]
    cve_id: Annotated[
        Optional[str],
        Field(
            default="CVE-2026-1234",
            description="Target vulnerability identifier",
            examples=["CVE-2026-1234"],
        ),
    ]
    candidate_control_ids: Annotated[
        Optional[List[str]],
        Field(
            default=None,
            description="List of control IDs to evaluate from catalog. If omitted, evaluates all 10 standard catalog controls.",
        ),
    ]
    custom_controls: Annotated[
        Optional[List[SecurityControl]],
        Field(
            default=None,
            description="Optional list of custom security controls to include in candidate pool.",
        ),
    ]
    existing_controls: Annotated[
        Optional[List[str]],
        Field(
            default_factory=list,
            description="List of control IDs already deployed in the enterprise, satisfying prerequisites.",
        ),
    ]
    # Risk Engine baseline parameters
    cvss: Annotated[
        Optional[float],
        Field(
            default=9.8,
            ge=0.0,
            le=10.0,
            description="NVD base CVSS score [0.0 - 10.0]",
            examples=[9.8],
        ),
    ]
    epss: Annotated[
        Optional[float],
        Field(
            default=0.82,
            ge=0.0,
            le=1.0,
            description="FIRST EPSS exploitation probability [0.0 - 1.0]",
            examples=[0.82],
        ),
    ]
    kev: Annotated[
        Optional[bool],
        Field(
            default=True,
            description="CISA KEV active exploitation indicator",
            examples=[True],
        ),
    ]
    internet_exposed: Annotated[
        Optional[bool],
        Field(
            default=True,
            description="Perimeter exposure indicator",
            examples=[True],
        ),
    ]
    criticality: Annotated[
        Optional[str],
        Field(
            default="Critical",
            description="Business criticality tier ('Critical', 'High', 'Medium', 'Low')",
            examples=["Critical"],
        ),
    ]
    # Financial CRQ baseline parameters
    revenue_loss_per_hour: Annotated[
        Optional[float],
        Field(
            default=250000.0,
            ge=0.0,
            description="Downtime revenue loss per hour",
            examples=[250000.0],
        ),
    ]
    downtime_hours: Annotated[
        Optional[float],
        Field(
            default=8.0,
            ge=0.0,
            description="Expected operational downtime hours per incident",
            examples=[8.0],
        ),
    ]
    incident_response_cost: Annotated[
        Optional[float],
        Field(
            default=150000.0,
            ge=0.0,
            description="Forensics and triage cost per incident",
            examples=[150000.0],
        ),
    ]
    recovery_cost: Annotated[
        Optional[float],
        Field(
            default=200000.0,
            ge=0.0,
            description="IT recovery and rebuild cost per incident",
            examples=[200000.0],
        ),
    ]
    regulatory_legal_cost: Annotated[
        Optional[float],
        Field(
            default=500000.0,
            ge=0.0,
            description="Regulatory fines and legal defense estimates",
            examples=[500000.0],
        ),
    ]
    customer_business_impact: Annotated[
        Optional[float],
        Field(
            default=300000.0,
            ge=0.0,
            description="Customer compensation, SLA penalties, and churn damages",
            examples=[300000.0],
        ),
    ]
    strategy: Annotated[
        Optional[str],
        Field(
            default="balanced_roi",
            description="Optimization objective ('balanced_roi', 'max_risk_reduction', 'cost_minimization')",
            examples=["balanced_roi"],
        ),
    ]
    record_to_decision_store: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to register this run into Decision Intelligence store for /decision/{id} querying",
        ),
    ]


class OptimizationRunResponse(BaseModel):
    """Unified Optimization Response contract matching exact problem specification."""

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "selected_controls": ["CTRL-MFA", "CTRL-EDR", "CTRL-PATCH", "CTRL-BACKUP"],
                "rejected_controls": ["CTRL-PAM", "CTRL-SIEM", "CTRL-ZTNA"],
                "total_cost": 1800000.0,
                "remaining_budget": 0.0,
                "baseline_risk": 91.5,
                "residual_risk": 24.3,
                "risk_reduction": 67.2,
                "baseline_eal": 4500000.0,
                "residual_eal": 980000.0,
                "financial_loss_avoided": 3520000.0,
                "selection_reasons": {
                    "CTRL-MFA": ["High modeled efficiency (ROSI: 2.1x)", "Satisfies budget constraint"],
                },
                "rejection_reasons": {
                    "CTRL-PAM": ["Exceeds remaining available budget"],
                },
                "model_version": "OPT-DET-1.0",
                "optimization_id": "OPT-RUN-2026-0001",
            }
        },
    )

    selected_controls: List[Any] = Field(
        description="Controls selected in the optimal portfolio (SecurityControl objects or control IDs)",
    )
    rejected_controls: List[Any] = Field(
        description="Candidate controls excluded due to budget, dependencies, or lower efficiency",
    )
    total_cost: float = Field(
        ge=0.0,
        description="Total monetary cost of selected controls",
    )
    remaining_budget: float = Field(
        ge=0.0,
        description="Unallocated budget remainder",
    )
    baseline_risk: float = Field(
        ge=0.0,
        description="Pre-intervention deterministic cyber risk score [0.0 - 100.0]",
    )
    residual_risk: float = Field(
        ge=0.0,
        description="Post-intervention residual cyber risk score [0.0 - 100.0]",
    )
    risk_reduction: float = Field(
        ge=0.0,
        description="Net reduction in cyber risk score (baseline_risk - residual_risk)",
    )
    baseline_eal: float = Field(
        ge=0.0,
        description="Pre-intervention Expected Annual Loss in currency units",
    )
    residual_eal: float = Field(
        ge=0.0,
        description="Post-intervention Expected Annual Loss in currency units",
    )
    financial_loss_avoided: float = Field(
        ge=0.0,
        description="Net monetary loss avoided per year (baseline_eal - residual_eal)",
    )
    selection_reasons: Dict[str, List[str]] = Field(
        description="Deterministic, evidence-based bullet reasons for each selected control",
    )
    rejection_reasons: Dict[str, List[str]] = Field(
        description="Deterministic reasons for each rejected control (budget, dependency, applicability)",
    )
    model_version: str = Field(
        default=OPTIMIZATION_MODEL_VERSION,
        description="Deterministic optimizer version",
    )
    optimization_id: str = Field(
        default="",
        description="Unique optimization identifier usable in /decision endpoints",
    )
    data_source: str = Field(
        default="actual_optimizer",
        description="Source of optimization data: 'actual_optimizer', 'benchmark', or 'manual'",
    )
    is_benchmark: bool = Field(
        default=False,
        description="Whether this response contains benchmark demonstration data",
    )
    assessment_id: Optional[str] = Field(
        default=None,
        description="Associated risk assessment identifier",
    )
    dependency_resolution: Optional[List[ControlDependencyResolution]] = Field(
        default=None,
        description="Detailed prerequisite dependency resolution items for evaluated controls",
    )


class RiskSnapshot(BaseModel):
    """Quantitative risk snapshot capturing scores and financial loss metrics."""

    risk_score: float
    risk_level: str
    likelihood: float
    impact: float
    expected_annual_loss: float
    total_loss_magnitude: float
    annual_event_frequency: float
    downtime_loss: float


class DeltaMetrics(BaseModel):
    """Deltas comparing baseline and residual states."""

    risk_reduction_points: float
    risk_reduction_percent: float
    financial_loss_avoided: float
    financial_loss_avoided_percent: float
    total_investment_cost: float
    net_annual_financial_benefit: float
    return_on_security_investment: float


class BeforeAfterRequest(BaseModel):
    """Request payload for detailed before-and-after quantitative portfolio comparison."""

    model_config = ConfigDict(extra="ignore")

    optimization_id: Optional[str] = Field(
        default=None,
        description="Existing optimization_id to query. If omitted, runs optimization using provided parameters.",
    )
    run_parameters: Optional[OptimizationRunRequest] = Field(
        default=None,
        description="Parameters to execute optimization if optimization_id is not supplied.",
    )


class BeforeAfterResponse(BaseModel):
    """Response contract for before-after comparative analysis."""

    model_config = ConfigDict(extra="ignore")

    optimization_id: str
    baseline: RiskSnapshot
    residual: RiskSnapshot
    deltas: DeltaMetrics
    controls_applied: List[str]
    model_version: str = OPTIMIZATION_MODEL_VERSION
    data_source: str = Field(
        default="actual_optimizer",
        description="Data source: 'actual_optimizer', 'benchmark', 'manual'",
    )
    is_benchmark: bool = Field(
        default=False,
        description="Whether this analysis is from benchmark data",
    )

