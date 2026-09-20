"""Pydantic Schemas for the Decision Intelligence Layer (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Defines structured data contracts for:
1. Alternative Portfolio Evaluation
2. Transparent Opportunity Cost Quantification
3. Marginal Budget Sensitivity Analytics
4. Explainable Selection/Rejection Evidence
"""

from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CandidateControl(BaseModel):
    """Specification of a security control candidate available for investment optimization."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    control_id: Annotated[
        str,
        Field(
            min_length=1,
            description="Unique identifier of the control (e.g. CTRL-MFA, CTRL-EDR)",
            examples=["CTRL-MFA"],
        ),
    ]
    name: Annotated[
        str,
        Field(
            min_length=1,
            description="Human-readable name of the cybersecurity control",
            examples=["Phishing-Resistant MFA"],
        ),
    ]
    cost: Annotated[
        float,
        Field(
            ge=0.0,
            description="Monetary cost to acquire, implement, and maintain the control",
            examples=[350000.0],
        ),
    ]
    risk_reduction: Annotated[
        float,
        Field(
            ge=0.0,
            description="Modeled monetary risk reduction (Expected Annual Loss reduction)",
            examples=[680000.0],
        ),
    ]
    workforce_hours: Annotated[
        float,
        Field(
            ge=0.0,
            description="Estimated engineering / operational labor hours required for rollout",
            examples=[80.0],
        ),
    ]
    implementation_days: Annotated[
        int,
        Field(
            ge=0,
            description="Estimated implementation elapsed duration in calendar days",
            examples=[14],
        ),
    ]
    applicable_assets: Annotated[
        List[str],
        Field(
            default_factory=list,
            description="List of asset identifiers protected by this control",
            examples=[["AST-001", "AST-002", "AST-003", "AST-004"]],
        ),
    ]
    critical_assets_covered: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            description="Count of high or critical tier enterprise assets covered",
            examples=[4],
        ),
    ]
    category: Annotated[
        str,
        Field(
            default="Technical",
            description="Control classification (e.g. Identity, Endpoint, Network, Governance, Cloud)",
            examples=["Identity & Access"],
        ),
    ]
    description: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Brief functional description of the control",
            examples=["Enforces FIDO2 hardware token multi-factor authentication across all identity providers."],
        ),
    ]


class ControlExplanation(BaseModel):
    """Structured evidence explaining why a specific control was selected or rejected."""

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "control": "MFA",
                "control_id": "CTRL-MFA",
                "selected": True,
                "cost": 350000.0,
                "risk_reduction": 680000.0,
                "reasons": [
                    "High modeled benefit (₹6,80,000 risk reduction)",
                    "Fits within budget (Cost: ₹3,50,000)",
                    "Applies to 4 critical assets",
                ],
            }
        },
    )

    control: Annotated[
        str,
        Field(
            description="Standardized or friendly control name (e.g. MFA, EDR)",
            examples=["MFA"],
        ),
    ]
    control_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Unique control identifier",
            examples=["CTRL-MFA"],
        ),
    ]
    selected: Annotated[
        bool,
        Field(
            description="True if the control is included in the portfolio; False if rejected",
            examples=[True],
        ),
    ]
    cost: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0.0,
            description="Cost of the control in configured currency",
            examples=[350000.0],
        ),
    ]
    risk_reduction: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0.0,
            description="Modeled risk reduction achieved by this control",
            examples=[680000.0],
        ),
    ]
    reasons: Annotated[
        List[str],
        Field(
            default_factory=list,
            description="Deterministic, evidence-based bullet reasons for selection or rejection",
            examples=[
                [
                    "High modeled benefit (₹6,80,000 risk reduction)",
                    "Fits within budget (Cost: ₹3,50,000)",
                    "Applies to 4 critical assets",
                ]
            ],
        ),
    ]


class AlternativePortfolio(BaseModel):
    """Structured portfolio option generated under specific investment objectives."""

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "portfolio_id": "portfolio-balanced-roi",
                "objective": "Balanced ROI & Cost-Efficiency",
                "total_cost": 1800000.0,
                "risk_reduction": 3250000.0,
                "residual_risk": 1750000.0,
                "workforce_hours": 410.0,
                "implementation_days": 28,
                "selected_controls": [
                    "Phishing-Resistant MFA",
                    "Next-Gen EDR",
                    "Automated Vulnerability & Patch Management",
                    "Immutable Cloud Backups",
                ],
                "is_selected": True,
                "roi": 1.81,
            }
        },
    )

    portfolio_id: Annotated[
        str,
        Field(
            description="Unique identifier for the portfolio option",
            examples=["portfolio-balanced-roi"],
        ),
    ]
    objective: Annotated[
        str,
        Field(
            description="Investment strategy or optimization objective",
            examples=["Balanced ROI & Cost-Efficiency"],
        ),
    ]
    total_cost: Annotated[
        float,
        Field(
            ge=0.0,
            description="Total monetary expenditure required for all selected controls",
            examples=[1800000.0],
        ),
    ]
    risk_reduction: Annotated[
        float,
        Field(
            ge=0.0,
            description="Total modeled monetary risk reduction achieved across assets",
            examples=[3250000.0],
        ),
    ]
    residual_risk: Annotated[
        float,
        Field(
            ge=0.0,
            description="Remaining modeled expected annual loss after portfolio implementation",
            examples=[1750000.0],
        ),
    ]
    workforce_hours: Annotated[
        float,
        Field(
            ge=0.0,
            description="Total engineering and operational hours required",
            examples=[410.0],
        ),
    ]
    implementation_days: Annotated[
        int,
        Field(
            ge=0,
            description="Estimated calendar days to complete all rollouts concurrently or sequentially",
            examples=[28],
        ),
    ]
    selected_controls: Annotated[
        List[str],
        Field(
            description="List of control names or IDs included in this portfolio",
            examples=[
                [
                    "Phishing-Resistant MFA",
                    "Next-Gen EDR",
                    "Automated Vulnerability & Patch Management",
                    "Immutable Cloud Backups",
                ]
            ],
        ),
    ]
    control_explanations: Annotated[
        Optional[List[ControlExplanation]],
        Field(
            default=None,
            description="Detailed evidence explanations for each candidate control under this portfolio",
        ),
    ]
    is_selected: Annotated[
        bool,
        Field(
            default=False,
            description="True if this portfolio is the primary selected/recommended portfolio",
            examples=[True],
        ),
    ]
    roi: Annotated[
        Optional[float],
        Field(
            default=None,
            description="Modeled Return on Security Investment: (risk_reduction - total_cost) / total_cost",
            examples=[1.81],
        ),
    ]


class AlternativesResponse(BaseModel):
    """Complete response payload for GET /decision/{optimization_id}/alternatives."""

    model_config = ConfigDict(
        extra="ignore",
    )

    optimization_id: Annotated[
        str,
        Field(
            description="Identifier of the referenced investment optimization",
            examples=["OPT-BENCHMARK-001"],
        ),
    ]
    baseline_risk: Annotated[
        float,
        Field(
            ge=0.0,
            description="Baseline Expected Annual Loss (EAL) before any control investment",
            examples=[5000000.0],
        ),
    ]
    budget_limit: Annotated[
        float,
        Field(
            ge=0.0,
            description="Configured investment budget ceiling",
            examples=[1800000.0],
        ),
    ]
    currency: Annotated[
        str,
        Field(
            default="INR",
            description="Monetary currency code",
            examples=["INR"],
        ),
    ]
    selected_portfolio_id: Annotated[
        str,
        Field(
            description="ID of the optimal/chosen portfolio",
            examples=["portfolio-balanced-roi"],
        ),
    ]
    alternatives: Annotated[
        List[AlternativePortfolio],
        Field(
            description="Structured list of alternative portfolios evaluated across strategic objectives",
        ),
    ]
    decision_summary: Annotated[
        str,
        Field(
            description="Executive summary synthesizing the portfolio trade-off landscape",
            examples=[
                "Portfolio 'portfolio-balanced-roi' is selected with ₹32,50,000 modeled risk reduction within ₹18,00,000 budget."
            ],
        ),
    ]


class OpportunityCostComparison(BaseModel):
    """Neutral comparison quantifying modeled risk reduction tradeoffs between two portfolios."""

    model_config = ConfigDict(
        extra="ignore",
    )

    compared_portfolio_id: Annotated[
        str,
        Field(
            description="ID of the alternative portfolio compared against the selected portfolio",
            examples=["portfolio-cost-constrained"],
        ),
    ]
    compared_objective: Annotated[
        str,
        Field(
            description="Objective of the compared portfolio",
            examples=["Cost-Constrained / Low Outlay"],
        ),
    ]
    selected_risk_reduction: Annotated[
        float,
        Field(
            description="Risk reduction of the selected portfolio",
            examples=[3250000.0],
        ),
    ]
    compared_risk_reduction: Annotated[
        float,
        Field(
            description="Risk reduction of the alternative portfolio",
            examples=[2200000.0],
        ),
    ]
    risk_reduction_difference: Annotated[
        float,
        Field(
            description="Modeled risk reduction difference: (compared_risk_reduction - selected_risk_reduction)",
            examples=[-1050000.0],
        ),
    ]
    cost_difference: Annotated[
        float,
        Field(
            description="Monetary cost difference: (compared_total_cost - selected_total_cost)",
            examples=[-850000.0],
        ),
    ]
    workforce_hours_difference: Annotated[
        float,
        Field(
            description="Workforce labor difference in hours",
            examples=[-180.0],
        ),
    ]
    implementation_days_difference: Annotated[
        int,
        Field(
            description="Implementation schedule timeline difference in days",
            examples=[-10],
        ),
    ]
    tradeoff_narrative: Annotated[
        str,
        Field(
            description="Neutral, objective statement quantifying sacrificed/gained reduction without subjective adjectives",
            examples=[
                "Under the same constraints, Portfolio Cost-Constrained provides ₹10,50,000 less modeled reduction than Portfolio Balanced ROI."
            ],
        ),
    ]
    controls_gained: Annotated[
        List[str],
        Field(
            default_factory=list,
            description="Controls included in the alternative portfolio that are not in the selected portfolio",
        ),
    ]
    controls_sacrificed: Annotated[
        List[str],
        Field(
            default_factory=list,
            description="Controls included in the selected portfolio that are omitted from the alternative portfolio",
        ),
    ]


class OpportunityCostResponse(BaseModel):
    """Complete response payload for GET /decision/{optimization_id}/opportunity-cost."""

    model_config = ConfigDict(
        extra="ignore",
    )

    optimization_id: Annotated[
        str,
        Field(
            description="Identifier of the optimization run",
            examples=["OPT-BENCHMARK-001"],
        ),
    ]
    selected_portfolio_id: Annotated[
        str,
        Field(
            description="ID of the selected benchmark portfolio",
            examples=["portfolio-balanced-roi"],
        ),
    ]
    selected_portfolio_name: Annotated[
        str,
        Field(
            description="Descriptive title of the selected portfolio",
            examples=["Balanced ROI & Cost-Efficiency"],
        ),
    ]
    selected_risk_reduction: Annotated[
        float,
        Field(
            description="Modeled risk reduction of the selected portfolio",
            examples=[3250000.0],
        ),
    ]
    selected_total_cost: Annotated[
        float,
        Field(
            description="Total cost of the selected portfolio",
            examples=[1800000.0],
        ),
    ]
    currency: Annotated[
        str,
        Field(
            default="INR",
            description="Monetary currency code",
            examples=["INR"],
        ),
    ]
    comparisons: Annotated[
        List[OpportunityCostComparison],
        Field(
            description="Pairwise opportunity cost comparisons across all alternative portfolios",
        ),
    ]
    summary_statement: Annotated[
        str,
        Field(
            description="Neutral high-level summary of modeled tradeoffs",
            examples=[
                "Comparing the selected portfolio against alternatives reveals modeled risk reduction tradeoffs ranging from -₹10,50,000 to +₹6,50,000 depending on capital allocation."
            ],
        ),
    ]
    assumptions: Annotated[
        List[str],
        Field(
            default_factory=list,
            description="Methodological modeling assumptions governing opportunity cost quantification",
        ),
    ]


class MarginalBudgetEvaluation(BaseModel):
    """Evaluation of risk reduction gained at a specific incremental budget increment."""

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "additional_budget": 500000.0,
                "additional_risk_reduction": 650000.0,
                "marginal_reduction_per_rupee": 1.30,
                "total_budget": 2300000.0,
                "total_risk_reduction": 3900000.0,
                "additional_controls_selected": ["Cloud Web Application Firewall & Bot Defense"],
                "efficiency_assessment": "High Marginal Return (1.30x)",
                "explanation": "An additional ₹5,00,000 budget enables Cloud WAF, capturing ₹6,50,000 extra modeled reduction across 3 internet-facing assets.",
            }
        },
    )

    additional_budget: Annotated[
        float,
        Field(
            ge=0.0,
            description="Additional budget increment evaluated (e.g. ₹5,00,000, ₹10,00,000, ₹25,00,000)",
            examples=[500000.0],
        ),
    ]
    additional_risk_reduction: Annotated[
        float,
        Field(
            ge=0.0,
            description="Incremental modeled risk reduction achieved with the additional budget",
            examples=[650000.0],
        ),
    ]
    marginal_reduction_per_rupee: Annotated[
        float,
        Field(
            ge=0.0,
            description="Marginal modeled reduction per additional rupee spent (additional_risk_reduction / additional_budget)",
            examples=[1.30],
        ),
    ]
    total_budget: Annotated[
        float,
        Field(
            ge=0.0,
            description="New total budget = base_budget + additional_budget",
            examples=[2300000.0],
        ),
    ]
    total_risk_reduction: Annotated[
        float,
        Field(
            ge=0.0,
            description="New total modeled risk reduction achieved under the augmented budget",
            examples=[3900000.0],
        ),
    ]
    additional_controls_selected: Annotated[
        List[str],
        Field(
            default_factory=list,
            description="Names of additional controls unlocked by the budget expansion",
            examples=[["Cloud Web Application Firewall & Bot Defense"]],
        ),
    ]
    efficiency_assessment: Annotated[
        str,
        Field(
            description="Deterministic evaluation of marginal efficiency (e.g. High Return, Moderate Return, Diminishing Return)",
            examples=["High Marginal Return (1.30x)"],
        ),
    ]
    explanation: Annotated[
        str,
        Field(
            description="Detailed deterministic narrative explaining the impact of the additional capital",
            examples=[
                "An additional ₹5,00,000 budget enables Cloud WAF, capturing ₹6,50,000 extra modeled reduction across 3 internet-facing assets."
            ],
        ),
    ]


class MarginalBudgetResponse(BaseModel):
    """Complete response payload for GET /decision/{optimization_id}/marginal-budget."""

    model_config = ConfigDict(
        extra="ignore",
    )

    optimization_id: Annotated[
        str,
        Field(
            description="Identifier of the baseline optimization",
            examples=["OPT-BENCHMARK-001"],
        ),
    ]
    base_budget: Annotated[
        float,
        Field(
            ge=0.0,
            description="Current baseline budget limit",
            examples=[1800000.0],
        ),
    ]
    base_risk_reduction: Annotated[
        float,
        Field(
            ge=0.0,
            description="Baseline modeled risk reduction achieved under current budget limit",
            examples=[3250000.0],
        ),
    ]
    currency: Annotated[
        str,
        Field(
            default="INR",
            description="Monetary currency code",
            examples=["INR"],
        ),
    ]
    evaluations: Annotated[
        List[MarginalBudgetEvaluation],
        Field(
            description="Sensitivity evaluations across requested additional budget levels (+₹5L, +₹10L, +₹25L)",
        ),
    ]
    diminishing_returns_observed: Annotated[
        bool,
        Field(
            description="True if marginal reduction per rupee decreases as budget escalates",
            examples=[True],
        ),
    ]
    recommendation: Annotated[
        str,
        Field(
            description="Actionable, deterministic capital allocation recommendation",
            examples=[
                "Expanding budget by +₹5,00,000 provides the steepest marginal efficiency (₹1.30 reduction per ₹1.00 spent)."
            ],
        ),
    ]


class OptimizationResult(BaseModel):
    """Stored or ingested complete cyber security investment optimization dataset."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    optimization_id: Annotated[
        str,
        Field(
            min_length=1,
            description="Unique identifier for this optimization scenario",
            examples=["OPT-BENCHMARK-001"],
        ),
    ]
    title: Annotated[
        str,
        Field(
            default="Enterprise Cyber Security Investment Optimization",
            description="Title or descriptive name of the optimization scenario",
        ),
    ]
    baseline_risk: Annotated[
        float,
        Field(
            gt=0.0,
            description="Total unmitigated baseline Expected Annual Loss (EAL)",
            examples=[5000000.0],
        ),
    ]
    budget_limit: Annotated[
        float,
        Field(
            ge=0.0,
            description="Configured investment budget limit",
            examples=[1800000.0],
        ),
    ]
    currency: Annotated[
        str,
        Field(
            default="INR",
            description="Monetary currency code",
            examples=["INR"],
        ),
    ]
    selected_portfolio_id: Annotated[
        str,
        Field(
            default="portfolio-balanced-roi",
            description="Default selected portfolio ID",
            examples=["portfolio-balanced-roi"],
        ),
    ]
    candidate_controls: Annotated[
        List[CandidateControl],
        Field(
            description="Set of candidate controls available for portfolio selection",
        ),
    ]
    custom_alternatives: Annotated[
        Optional[List[AlternativePortfolio]],
        Field(
            default=None,
            description="Optional pre-computed alternative portfolios; if omitted, alternatives will be generated dynamically",
        ),
    ]
    created_at: Annotated[
        Optional[str],
        Field(
            default=None,
            description="ISO timestamp when optimization was executed",
        ),
    ]


class DecisionHealthResponse(BaseModel):
    """Health check response for the Decision Intelligence Layer."""

    status: str = Field(default="ok", examples=["ok"])
    module: str = Field(default="decision-intelligence", examples=["decision-intelligence"])
    model_version: str = Field(default="DECISION-INTEL-1.0", examples=["DECISION-INTEL-1.0"])
    seeded_optimizations: int = Field(default=1, examples=[1])
