"""Pydantic Schemas for Continuous Re-Optimization Orchestration (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Defines structured data contracts for:
1. Re-Optimization Trigger Requests
2. Differential Risk & Financial Impact Responses
3. Control Portfolio Transition Summaries
4. Provenance Anchoring & Health Diagnostics
"""

from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from blockchain.schemas import BlockchainReceipt


class ReoptimizeRequest(BaseModel):
    """Trigger payload to initiate continuous re-optimization across the quantitative pipeline."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    asset_id: Annotated[
        Optional[str],
        Field(
            default="AST-001",
            description="Identifier of target asset (e.g. AST-001, AST-BANK-CORE). If omitted, defaults to primary benchmark asset.",
            examples=["AST-001"],
        ),
    ]
    cve_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Vulnerability CVE identifier (e.g. CVE-2026-1234, CVE-2021-44228)",
            examples=["CVE-2026-1234"],
        ),
    ]
    optimization_id: Annotated[
        Optional[str],
        Field(
            default="OPT-BENCHMARK-001",
            description="Baseline investment optimization scenario identifier to compare against",
            examples=["OPT-BENCHMARK-001"],
        ),
    ]
    epss: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0.0,
            le=1.0,
            description="Updated EPSS exploitation probability score [0.0 - 1.0]",
            examples=[0.92],
        ),
    ]
    kev: Annotated[
        Optional[bool],
        Field(
            default=None,
            description="Updated CISA KEV catalog active exploitation status flag",
            examples=[True],
        ),
    ]
    cvss: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0.0,
            le=10.0,
            description="Updated NVD base CVSS score [0.0 - 10.0]",
            examples=[9.8],
        ),
    ]
    internet_exposed: Annotated[
        Optional[bool],
        Field(
            default=None,
            description="Updated perimeter exposure status for the asset",
            examples=[True],
        ),
    ]
    criticality: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Updated asset business criticality tier ('Critical', 'High', 'Medium', 'Low')",
            examples=["Critical"],
        ),
    ]
    is_patched: Annotated[
        Optional[bool],
        Field(
            default=None,
            description="Remediation/patch status flag. Setting to True reflects successful patch deployment.",
            examples=[True],
        ),
    ]
    budget_limit: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0.0,
            description="Updated capital allocation ceiling for cybersecurity control optimization",
            examples=[2500000.0],
        ),
    ]
    revenue_loss_per_hour: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0.0,
            description="Updated downtime financial cost per hour for financial CRQ",
            examples=[200000.0],
        ),
    ]
    downtime_hours: Annotated[
        Optional[float],
        Field(
            default=None,
            ge=0.0,
            description="Updated estimated downtime outage hours",
            examples=[12.0],
        ),
    ]
    record_provenance: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to anchor the new re-optimization decision to the blockchain provenance ledger",
        ),
    ]
    iterations: Annotated[
        int,
        Field(
            default=1000,
            ge=100,
            le=50000,
            description="Monte Carlo stochastic trial count",
        ),
    ]
    seed: Annotated[
        Optional[int],
        Field(
            default=42,
            description="Deterministic random seed for reproducible Monte Carlo simulation",
        ),
    ]


class PortfolioDeltaSummary(BaseModel):
    """Comparative delta analysis between previous and new investment decisions."""

    model_config = ConfigDict(extra="ignore")

    previous_portfolio_id: str = Field(description="Previous baseline portfolio identifier")
    new_portfolio_id: str = Field(description="New re-optimized portfolio identifier")
    previous_cost: float = Field(description="Previous total implementation cost")
    new_cost: float = Field(description="New total implementation cost")
    cost_delta: float = Field(description="Net difference in capital expenditure (+/-)")
    previous_risk_reduction: float = Field(description="Previous modeled monetary risk reduction")
    new_risk_reduction: float = Field(description="New modeled monetary risk reduction")
    risk_reduction_delta: float = Field(description="Net difference in risk reduction achieved")
    previous_controls: List[str] = Field(description="List of control IDs selected previously")
    new_controls: List[str] = Field(description="List of control IDs selected in new decision")
    controls_added: List[str] = Field(description="Newly selected controls not in previous portfolio")
    controls_removed: List[str] = Field(description="De-prioritized controls removed from previous portfolio")
    portfolio_changed: bool = Field(description="True if control composition or investment level shifted")


class ReoptimizeResponse(BaseModel):
    """Complete response contract returned by the Continuous Re-Optimization Orchestration Layer."""

    model_config = ConfigDict(extra="ignore")

    reoptimization_id: str = Field(description="Unique identifier for this re-optimization event")
    asset_id: str = Field(description="Primary affected asset identifier")
    cve_id: str = Field(description="Associated CVE vulnerability identifier")
    status: str = Field(description="Execution status ('REOPTIMIZATION_COMPLETE', 'NO_CHANGE_DETECTED')")
    timestamp: str = Field(description="ISO-8601 UTC timestamp of the re-optimization")
    change_reasons: List[str] = Field(
        description="List of concrete, detected parameter changes triggering the re-calculation (no invented text)"
    )
    previous_risk: Dict[str, Any] = Field(
        description="Previous deterministic cyber risk metrics (score, level, likelihood, impact)"
    )
    new_risk: Dict[str, Any] = Field(
        description="New deterministic cyber risk metrics after parameter recalculation"
    )
    risk_delta: float = Field(description="Net change in risk score (new_risk_score - previous_risk_score)")
    previous_crq_eal: float = Field(description="Previous Expected Annual Loss (EAL)")
    new_crq_eal: float = Field(description="New Expected Annual Loss (EAL)")
    crq_eal_delta: float = Field(description="Net change in Expected Annual Loss (+/-)")
    previous_p95: float = Field(description="Previous Monte Carlo P95 catastrophic loss metric")
    new_p95: float = Field(description="New Monte Carlo P95 catastrophic loss metric")
    p95_delta: float = Field(description="Net difference in P95 loss metric")
    previous_portfolio: Dict[str, Any] = Field(description="Previous control portfolio details")
    new_portfolio: Dict[str, Any] = Field(description="New optimal control portfolio details")
    portfolio_delta: PortfolioDeltaSummary = Field(description="Structured comparison of control choices")
    new_optimization_id: str = Field(description="Newly registered optimization identifier")
    assessment_id: str = Field(description="Assessment identifier associated with this decision")
    provenance_recorded: bool = Field(description="True if newly anchored to the blockchain provenance ledger")
    blockchain_receipt: Optional[BlockchainReceipt] = Field(
        default=None,
        description="Immutable cryptographic transaction receipt if provenance recording was enabled",
    )


class OrchestrationHealthResponse(BaseModel):
    """Operational health diagnostic for continuous re-optimization."""

    model_config = ConfigDict(extra="ignore")

    status: str = Field(default="ok")
    module: str = Field(default="continuous-reoptimization")
    version: str = Field(default="REOPT-1.0")
    tracked_assets_count: int = Field(description="Number of assets tracked in continuous inventory")
    total_reoptimizations_executed: int = Field(description="Cumulative count of re-optimizations triggered")
