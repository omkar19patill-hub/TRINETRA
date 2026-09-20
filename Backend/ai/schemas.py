"""Pydantic Schemas for the Explainable AI Layer (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Defines strict structured context models and response contracts for board-ready,
hallucination-free natural-language explanations.
"""

from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AssetContext(BaseModel):
    """Contextual metadata for the target asset under analysis."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    asset_id: Annotated[str, Field(description="Unique asset identifier", examples=["AST-001"])]
    asset_name: Annotated[Optional[str], Field(default=None, description="Human-readable asset title")]
    criticality: Annotated[str, Field(default="High", description="Enterprise criticality tier", examples=["Critical"])]
    internet_exposed: Annotated[bool, Field(default=False, description="Perimeter exposure flag")]
    cve_id: Annotated[Optional[str], Field(default=None, description="Associated CVE identifier", examples=["CVE-2026-1234"])]
    asset_type: Annotated[Optional[str], Field(default=None, description="Infrastructure role", examples=["Application Gateway"])]
    business_service: Annotated[Optional[str], Field(default=None, description="Dependent business process", examples=["Payment Gateway"])]


class RiskContext(BaseModel):
    """Deterministic risk quantification outputs from the Cyber Risk Engine."""

    model_config = ConfigDict(extra="ignore")

    risk_score: Annotated[float, Field(ge=0.0, le=100.0, description="Composite cyber risk score [0 - 100]")]
    risk_level: Annotated[str, Field(description="Categorical risk tier", examples=["Critical", "High"])]
    cvss: Annotated[float, Field(ge=0.0, le=10.0, description="Base CVSS score")]
    epss: Annotated[float, Field(ge=0.0, le=1.0, description="FIRST EPSS exploit probability")]
    kev: Annotated[bool, Field(description="CISA Known Exploited Vulnerability flag")]
    drivers: Annotated[Optional[List[str]], Field(default_factory=list, description="Key deterministic risk drivers")]


class FinancialCRQContext(BaseModel):
    """Financial cyber-risk quantification metrics from Open FAIR module."""

    model_config = ConfigDict(extra="ignore")

    downtime_loss: Annotated[float, Field(ge=0.0, description="Modeled downtime outage loss")]
    incident_response_cost: Annotated[float, Field(default=0.0, ge=0.0, description="Incident response cost")]
    recovery_cost: Annotated[float, Field(default=0.0, ge=0.0, description="Recovery & system rebuild cost")]
    regulatory_legal_cost: Annotated[float, Field(default=0.0, ge=0.0, description="Regulatory and legal cost")]
    customer_business_impact: Annotated[float, Field(default=0.0, ge=0.0, description="Customer SLA & churn impact")]
    total_loss_magnitude: Annotated[float, Field(ge=0.0, description="Total modeled financial loss per event")]
    annual_event_frequency: Annotated[float, Field(ge=0.0, description="Modeled loss event frequency (events/year)")]
    expected_annual_loss: Annotated[float, Field(ge=0.0, description="Expected Annual Loss (EAL)")]
    currency: Annotated[str, Field(default="INR", description="Currency code")]


class MonteCarloContext(BaseModel):
    """Stochastic loss distribution metrics from Monte Carlo Simulation engine."""

    model_config = ConfigDict(extra="ignore")

    mean_annual_loss: Annotated[Optional[float], Field(default=None, ge=0.0, description="Simulated mean annual loss")]
    p50_loss: Annotated[Optional[float], Field(default=None, ge=0.0, description="P50 (Median) simulated loss")]
    p75_loss: Annotated[Optional[float], Field(default=None, ge=0.0, description="P75 simulated loss")]
    p90_loss: Annotated[Optional[float], Field(default=None, ge=0.0, description="P90 (1-in-10 year VaR) simulated loss")]
    p95_loss: Annotated[Optional[float], Field(default=None, ge=0.0, description="P95 simulated loss")]
    p99_loss: Annotated[Optional[float], Field(default=None, ge=0.0, description="P99 (Catastrophic tail) simulated loss")]
    iterations: Annotated[int, Field(default=10000, description="Number of simulation trials")]
    currency: Annotated[str, Field(default="INR", description="Currency code")]


class OptimizationContext(BaseModel):
    """Investment optimization outputs."""

    model_config = ConfigDict(extra="ignore")

    optimization_id: Annotated[str, Field(description="Optimization scenario ID", examples=["OPT-BENCHMARK-001"])]
    budget_limit: Annotated[float, Field(ge=0.0, description="Configured budget ceiling")]
    selected_portfolio_id: Annotated[str, Field(description="Selected portfolio ID")]
    selected_controls: Annotated[List[str], Field(description="List of selected control names")]
    total_cost: Annotated[float, Field(ge=0.0, description="Total cost of selected portfolio")]
    risk_reduction: Annotated[float, Field(ge=0.0, description="Modeled risk reduction achieved")]
    residual_risk: Annotated[float, Field(ge=0.0, description="Residual modeled risk remaining")]
    currency: Annotated[str, Field(default="INR", description="Currency code")]


class DecisionContext(BaseModel):
    """Decision Intelligence Layer analytics."""

    model_config = ConfigDict(extra="ignore")

    alternative_portfolios: Annotated[Optional[List[Dict[str, Any]]], Field(default_factory=list)]
    opportunity_cost_comparisons: Annotated[Optional[List[Dict[str, Any]]], Field(default_factory=list)]
    marginal_budget_evaluations: Annotated[Optional[List[Dict[str, Any]]], Field(default_factory=list)]
    control_explanations: Annotated[Optional[List[Dict[str, Any]]], Field(default_factory=list)]


class MLContext(BaseModel):
    """Auxiliary Machine Learning classification signal."""

    model_config = ConfigDict(extra="ignore")

    ml_risk_probability: Annotated[float, Field(ge=0.0, le=1.0, description="Auxiliary risk probability")]
    predicted_class: Annotated[int, Field(description="Binary classification outcome (0 or 1)")]
    classification_label: Annotated[str, Field(description="Human readable label")]
    feature_contributions: Annotated[Optional[List[Dict[str, Any]]], Field(default_factory=list)]


class EvidenceContext(BaseModel):
    """Threat intelligence source and freshness provenance."""

    model_config = ConfigDict(extra="ignore")

    sources: Annotated[List[str], Field(default_factory=lambda: ["NVD", "EPSS", "CISA_KEV"])]
    freshness: Annotated[Optional[Dict[str, Any]], Field(default=None)]
    mitre_attack: Annotated[Optional[Dict[str, Any]], Field(default=None)]


class StructuredContext(BaseModel):
    """Unified container aggregating all active backend engine outputs.

    Acts as the single source of truth for the Explainable AI Layer.
    """

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "asset": {
                    "asset_id": "AST-001",
                    "criticality": "Critical",
                    "internet_exposed": True,
                    "cve_id": "CVE-2026-1234",
                    "asset_type": "Application Gateway",
                    "business_service": "Payment Gateway",
                },
                "risk": {
                    "risk_score": 96.5,
                    "risk_level": "Critical",
                    "cvss": 9.8,
                    "epss": 0.82,
                    "kev": True,
                },
                "financial_crq": {
                    "downtime_loss": 400000.0,
                    "total_loss_magnitude": 825000.0,
                    "annual_event_frequency": 0.82,
                    "expected_annual_loss": 676500.0,
                    "currency": "INR",
                },
                "monte_carlo": {
                    "mean_annual_loss": 684200.0,
                    "p50_loss": 650000.0,
                    "p90_loss": 1240000.0,
                    "p99_loss": 2180000.0,
                    "iterations": 10000,
                    "currency": "INR",
                },
            }
        },
    )

    asset: Optional[AssetContext] = None
    risk: Optional[RiskContext] = None
    financial_crq: Optional[FinancialCRQContext] = None
    monte_carlo: Optional[MonteCarloContext] = None
    optimization: Optional[OptimizationContext] = None
    decision: Optional[DecisionContext] = None
    ml: Optional[MLContext] = None
    evidence_metadata: Optional[EvidenceContext] = None


class AIExplanationRequest(BaseModel):
    """Input payload for Explainable AI queries."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "prompt": "Why is this asset categorized as high risk?",
                "context": {
                    "asset": {
                        "asset_id": "AST-001",
                        "criticality": "Critical",
                        "internet_exposed": True,
                        "cve_id": "CVE-2026-1234",
                    },
                    "risk": {
                        "risk_score": 96.5,
                        "risk_level": "Critical",
                        "cvss": 9.8,
                        "epss": 0.82,
                        "kev": True,
                    },
                    "financial_crq": {
                        "downtime_loss": 400000.0,
                        "total_loss_magnitude": 825000.0,
                        "annual_event_frequency": 0.82,
                        "expected_annual_loss": 676500.0,
                        "currency": "INR",
                    },
                },
            }
        },
    )

    prompt: Annotated[Optional[str], Field(default=None, description="Natural language question or prompt")]
    context: Annotated[StructuredContext, Field(description="Structured backend context object (source of truth)")]
    target_focus: Annotated[Optional[str], Field(default=None, description="Optional focus area (risk, optimization, scenario, ml)")]


class EvidenceItem(BaseModel):
    """Traceable, verifiable evidence point from a specific backend module."""

    source_module: Annotated[str, Field(description="Backend module providing the fact", examples=["Risk Engine", "Financial CRQ"])]
    metric: Annotated[str, Field(description="Name of the grounded metric", examples=["Expected Annual Loss (EAL)"])]
    value: Annotated[Any, Field(description="Grounded metric value", examples=["₹6,76,500"])]
    context_note: Annotated[str, Field(description="Factual context note")]


class AIExplanationResponse(BaseModel):
    """Complete output contract for Explainable AI endpoints."""

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "answer": "Asset AST-001 is categorized as Critical Risk (Score: 96.5/100) due to an unauthenticated RCE vulnerability (CVE-2026-1234, CVSS 9.8) with active in-the-wild exploitation (CISA KEV) on an internet-facing perimeter gateway protecting the Payment Gateway. The modeled Expected Annual Loss is ₹6,76,500 with a 1-in-10 year VaR (P90) of ₹12,40,000.",
                "key_facts": [
                    "Technical Severity: CVSS 9.8 (Critical RCE)",
                    "Exploit Probability: EPSS 82.0% with active CISA KEV listing",
                    "Asset Perimeter: Internet Exposed Critical asset (Payment Gateway)",
                    "Financial Exposure: Expected Annual Loss of ₹6,76,500.00",
                    "Tail Risk: P90 1-in-10 yr loss of ₹12,40,000.00 (Monte Carlo 10,000 iterations)",
                ],
                "evidence": [
                    {
                        "source_module": "Risk Engine",
                        "metric": "Composite Risk Score",
                        "value": 96.5,
                        "context_note": "Deterministic score synthesized from CVSS 9.8, EPSS 0.82, KEV True, Exposure True",
                    },
                    {
                        "source_module": "Financial CRQ",
                        "metric": "Expected Annual Loss",
                        "value": "₹6,76,500.00",
                        "context_note": "Open FAIR expectation: 0.82 events/yr × ₹8,25,000 loss magnitude",
                    },
                ],
                "assumptions": [
                    "Explanations are strictly grounded in deterministic backend outputs.",
                    "No financial or risk values are generated or modified by generative AI.",
                    "Monetary figures represent modeled mathematical expectations under Open FAIR / Monte Carlo assumptions.",
                ],
                "model_versions": {
                    "ai_engine": "AI-EXPLAIN-1.0",
                    "risk_engine": "RISK-SCORE-MVP-1.0",
                    "financial_crq": "CRQ-MVP-1.0",
                    "monte_carlo": "MONTE-CARLO-MVP-1.0",
                    "decision_intelligence": "DECISION-INTEL-1.0",
                    "ml_calibration": "ML-CALIBRATION-LOGREG-1.0",
                },
            }
        },
    )

    answer: Annotated[str, Field(description="Clear, executive board-ready explanation strictly grounded in provided facts")]
    key_facts: Annotated[List[str], Field(description="Bullet points of verifiable grounding facts extracted from context")]
    evidence: Annotated[List[EvidenceItem], Field(description="Attributed evidence records with source modules")]
    assumptions: Annotated[List[str], Field(description="Transparent modeling assumptions and boundaries")]
    model_versions: Annotated[Dict[str, str], Field(description="Active versions across all underlying engines")]


class AIHealthResponse(BaseModel):
    """Health check response for Explainable AI module."""

    status: str = Field(default="ok", examples=["ok"])
    module: str = Field(default="explainable-ai", examples=["explainable-ai"])
    model_version: str = Field(default="AI-EXPLAIN-1.0", examples=["AI-EXPLAIN-1.0"])
    grounding_enforced: bool = Field(default=True, examples=[True])
