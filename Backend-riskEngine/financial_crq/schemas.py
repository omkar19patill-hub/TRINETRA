"""Pydantic Schemas for the Financial Cyber Risk Quantification (CRQ) Layer

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Defines request/response contracts, data validation rules, loss component breakdowns,
and hand-off schemas for the downstream Monte Carlo simulation engine (DEV 2).
"""

from typing import Annotated, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


VALID_CRITICALITIES = {"Critical", "High", "Medium", "Low"}


class FinancialCRQInput(BaseModel):
    """Input contract for Financial Cyber Risk Quantification.

    Combines cyber risk scoring metrics (likelihood, risk score, criticality)
    with business impact and financial cost parameters (revenue loss rate, downtime,
    forensics, recovery, legal, customer impact).
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "asset_id": "AST-001",
                "cve_id": "CVE-001",
                "likelihood": 0.40,
                "risk_score": 60.0,
                "criticality": "High",
                "revenue_loss_per_hour": 50000.0,
                "downtime_hours": 8.0,
                "incident_response_cost": 100000.0,
                "recovery_cost": 200000.0,
                "regulatory_legal_cost": 50000.0,
                "customer_business_impact": 75000.0,
                "baseline_annual_frequency": 1.0,
                "currency": "INR",
            }
        },
    )

    asset_id: Annotated[
        str,
        Field(
            min_length=1,
            description="Unique identifier of the target asset (e.g. AST-001)",
            examples=["AST-001"],
        ),
    ]
    cve_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Common Vulnerabilities and Exposures (CVE) identifier",
            examples=["CVE-001"],
        ),
    ]
    likelihood: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Exploitation likelihood score [0.0 - 1.0] from Cyber Risk Engine",
            examples=[0.40],
        ),
    ]
    risk_score: Annotated[
        float,
        Field(
            ge=0.0,
            le=100.0,
            description="Composite cyber risk score [0.0 - 100.0] from Cyber Risk Engine",
            examples=[60.0],
        ),
    ]
    criticality: Annotated[
        str,
        Field(
            description="Asset business criticality rating: 'Critical', 'High', 'Medium', or 'Low'",
            examples=["High"],
        ),
    ]
    revenue_loss_per_hour: Annotated[
        float,
        Field(
            ge=0.0,
            description="Estimated business revenue lost per hour of operational outage",
            examples=[50000.0],
        ),
    ]
    downtime_hours: Annotated[
        float,
        Field(
            ge=0.0,
            description="Estimated operational downtime / service outage duration in hours",
            examples=[8.0],
        ),
    ]
    incident_response_cost: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            description="Estimated direct forensics, incident triage, and response engagement costs",
            examples=[100000.0],
        ),
    ]
    recovery_cost: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            description="Estimated system restoration, data reconstruction, and backup recovery costs",
            examples=[200000.0],
        ),
    ]
    regulatory_legal_cost: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            description="Estimated regulatory penalties, legal retainers, notification compliance fees",
            examples=[50000.0],
        ),
    ]
    customer_business_impact: Annotated[
        float,
        Field(
            default=0.0,
            ge=0.0,
            description="Estimated SLA penalties, customer churn, churn mitigation, reputation cost",
            examples=[75000.0],
        ),
    ]
    baseline_annual_frequency: Annotated[
        float,
        Field(
            default=1.0,
            ge=0.0,
            description="Configurable baseline annual attack attempt frequency assumption (events/year)",
            examples=[1.0],
        ),
    ]
    currency: Annotated[
        str,
        Field(
            default="INR",
            min_length=1,
            description="Currency code for monetary reporting (e.g. INR, USD, EUR)",
            examples=["INR"],
        ),
    ]

    @field_validator("criticality")
    @classmethod
    def validate_criticality(cls, value: str) -> str:
        """Validate that criticality strictly adheres to enterprise tiers."""
        formatted = value.strip().capitalize() if isinstance(value, str) else value
        if formatted not in VALID_CRITICALITIES:
            raise ValueError(
                f"Invalid criticality '{value}'. Accepted values are: {', '.join(sorted(VALID_CRITICALITIES))}"
            )
        return formatted


class LossComponents(BaseModel):
    """Detailed breakdown of individual financial loss components per cyber event."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "downtime_loss": 400000.0,
                "incident_response_cost": 100000.0,
                "recovery_cost": 200000.0,
                "regulatory_legal_cost": 50000.0,
                "customer_business_impact": 75000.0,
                "total_loss_magnitude": 825000.0,
            }
        }
    )

    downtime_loss: float = Field(
        description="Calculated downtime loss = revenue_loss_per_hour × downtime_hours"
    )
    incident_response_cost: float = Field(
        description="Direct incident response & forensics cost"
    )
    recovery_cost: float = Field(
        description="System recovery, data rebuild, and IT restoration cost"
    )
    regulatory_legal_cost: float = Field(
        description="Regulatory fines, compliance sanctions, and legal defense fees"
    )
    customer_business_impact: float = Field(
        description="Customer compensation, SLA penalties, and business reputation impact"
    )
    total_loss_magnitude: float = Field(
        description="Total modeled loss per single security breach event (sum of all components)"
    )


class MonteCarloInput(BaseModel):
    """Data contract prepared for DEV 2's Monte Carlo Simulation Engine.

    Exposes baseline deterministic financial parameters and event frequencies
    which DEV 2 will parameterize with probability distributions (e.g. PERT,
    Lognormal, Poisson) for stochastic simulation.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "AST-001",
                "cve_id": "CVE-001",
                "annual_frequency_assumption": 0.40,
                "downtime_hours": 8.0,
                "revenue_loss_per_hour": 50000.0,
                "incident_response_cost": 100000.0,
                "recovery_cost": 200000.0,
                "regulatory_legal_cost": 50000.0,
                "customer_business_impact": 75000.0,
                "loss_magnitude": 825000.0,
                "baseline_annual_frequency": 1.0,
                "likelihood": 0.40,
                "currency": "INR",
            }
        }
    )

    asset_id: str = Field(description="Target asset identifier")
    cve_id: Optional[str] = Field(default=None, description="Target CVE identifier")
    annual_frequency_assumption: float = Field(
        description="Modeled annual loss event frequency (baseline_annual_frequency × likelihood)"
    )
    downtime_hours: float = Field(
        description="Expected downtime hours for simulation distribution"
    )
    revenue_loss_per_hour: float = Field(
        description="Hourly revenue impact rate"
    )
    incident_response_cost: float = Field(
        description="Baseline incident response cost"
    )
    recovery_cost: float = Field(
        description="Baseline recovery and restoration cost"
    )
    regulatory_legal_cost: float = Field(
        description="Baseline legal, compliance, and regulatory liability cost"
    )
    customer_business_impact: float = Field(
        description="Baseline customer compensation and SLA impact cost"
    )
    loss_magnitude: float = Field(
        description="Total baseline loss magnitude per event"
    )
    baseline_annual_frequency: float = Field(
        description="Baseline annual frequency factor"
    )
    likelihood: float = Field(
        description="Cyber risk likelihood score [0.0 - 1.0]"
    )
    currency: str = Field(
        default="INR",
        description="Currency code for simulated financial distributions"
    )


class FinancialCRQResult(BaseModel):
    """Complete output contract of the Financial Cyber Risk Quantification (CRQ) Layer."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "AST-001",
                "cve_id": "CVE-001",
                "likelihood": 0.40,
                "baseline_annual_frequency": 1.0,
                "annual_event_frequency": 0.40,
                "downtime_loss": 400000.0,
                "incident_response_cost": 100000.0,
                "recovery_cost": 200000.0,
                "regulatory_legal_cost": 50000.0,
                "customer_business_impact": 75000.0,
                "total_loss_magnitude": 825000.0,
                "expected_annual_loss": 330000.0,
                "currency": "INR",
                "assumptions": [
                    "Baseline annual frequency (1.00 events/yr) is a configurable prototype modeling assumption.",
                    "Likelihood (0.40) is derived from technical CVSS/EPSS/KEV indicators and is not a guaranteed empirical probability.",
                    "All monetary and downtime values are organization-provided estimates or synthetic demonstration values.",
                    "Expected Annual Loss (EAL = ₹330,000.00) represents a modeled mathematical expectation under assumptions, not a guaranteed prediction."
                ],
                "model_version": "CRQ-MVP-1.0",
                "explanation": [
                    "Modeled event frequency: 0.40 events/year (Likelihood: 0.40 × Baseline frequency: 1.00 events/yr)",
                    "Downtime loss: ₹400,000.00 (8.00 hrs × ₹50,000.00/hr)",
                    "Incident response cost: ₹100,000.00",
                    "Recovery cost: ₹200,000.00",
                    "Regulatory & legal cost: ₹50,000.00",
                    "Customer & business impact: ₹75,000.00",
                    "Total modeled loss per event (Loss Magnitude): ₹825,000.00",
                    "Expected Annual Loss (EAL): ₹330,000.00 (0.40 events/yr × ₹825,000.00/event)"
                ],
                "monte_carlo_input": {
                    "asset_id": "AST-001",
                    "cve_id": "CVE-001",
                    "annual_frequency_assumption": 0.40,
                    "downtime_hours": 8.0,
                    "revenue_loss_per_hour": 50000.0,
                    "incident_response_cost": 100000.0,
                    "recovery_cost": 200000.0,
                    "regulatory_legal_cost": 50000.0,
                    "customer_business_impact": 75000.0,
                    "loss_magnitude": 825000.0,
                    "baseline_annual_frequency": 1.0,
                    "likelihood": 0.40,
                    "currency": "INR",
                },
            }
        }
    )

    asset_id: str = Field(description="Target asset identifier")
    cve_id: Optional[str] = Field(default=None, description="Vulnerability identifier")
    likelihood: float = Field(description="Exploitation likelihood score [0.0 - 1.0]")
    baseline_annual_frequency: float = Field(
        description="Configured baseline annual frequency factor (events/year)"
    )
    annual_event_frequency: float = Field(
        description="Modeled annual loss event frequency = baseline_annual_frequency × likelihood"
    )

    # Loss components
    downtime_loss: float = Field(description="Revenue loss caused by operational downtime")
    incident_response_cost: float = Field(description="Incident response and investigation cost")
    recovery_cost: float = Field(description="IT system recovery and data restoration cost")
    regulatory_legal_cost: float = Field(description="Regulatory fines and legal defense cost")
    customer_business_impact: float = Field(description="SLA breach penalties and customer churn impact")
    total_loss_magnitude: float = Field(
        description="Total modeled financial loss per single security incident"
    )

    # Financial Quantification
    expected_annual_loss: float = Field(
        description="Expected Annual Loss (EAL) = Annual Event Frequency × Total Loss Magnitude"
    )
    currency: str = Field(default="INR", description="Currency code for financial reporting")

    # Governance & Transparency
    assumptions: List[str] = Field(
        description="Transparent declarations of modeling assumptions and prototype parameters"
    )
    model_version: str = Field(
        default="CRQ-MVP-1.0",
        description="Financial CRQ model version identifier"
    )
    explanation: List[str] = Field(
        description="Step-by-step deterministic explainability breakdown for board reporting"
    )

    # Hand-off interface for DEV 2
    monte_carlo_input: MonteCarloInput = Field(
        description="Structured input payload designed for DEV 2's Monte Carlo simulation engine"
    )


class FinancialCRQHealthResponse(BaseModel):
    """Health check response schema for Financial CRQ module."""

    status: str = Field(default="ok", examples=["ok"])
    module: str = Field(default="financial-crq", examples=["financial-crq"])
    model_version: str = Field(default="CRQ-MVP-1.0", examples=["CRQ-MVP-1.0"])
