"""Pydantic Schemas for the Monte Carlo Simulation Layer

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Stochastic Uncertainty & Monte Carlo Simulation Engine

Defines input contracts for parameter uncertainty, simulation configuration,
distribution output percentiles (P50, P75, P90, P95, P99), histogram binning,
and integration bridges with DEV 1's Financial CRQ layer.
"""

from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from financial_crq.schemas import FinancialCRQInput, MonteCarloInput as Dev1MonteCarloInput


class MonteCarloInput(BaseModel):
    """Input payload for Monte Carlo Cyber Risk Simulation.

    Defines uncertainty ranges (min, mode, max) for event frequency and
    component-wise financial costs to execute stochastic simulation.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "asset_id": "AST-001",
                "cve_id": "CVE-001",
                "iterations": 10000,
                "seed": 42,
                "currency": "INR",
                "frequency_min": 0.20,
                "frequency_mode": 0.40,
                "frequency_max": 0.80,
                "downtime_hours_min": 4.0,
                "downtime_hours_mode": 8.0,
                "downtime_hours_max": 24.0,
                "revenue_loss_per_hour_min": 30000.0,
                "revenue_loss_per_hour_mode": 50000.0,
                "revenue_loss_per_hour_max": 75000.0,
                "incident_response_cost_min": 50000.0,
                "incident_response_cost_mode": 100000.0,
                "incident_response_cost_max": 180000.0,
                "recovery_cost_min": 100000.0,
                "recovery_cost_mode": 200000.0,
                "recovery_cost_max": 350000.0,
                "regulatory_legal_cost_min": 20000.0,
                "regulatory_legal_cost_mode": 50000.0,
                "regulatory_legal_cost_max": 120000.0,
                "customer_business_impact_min": 30000.0,
                "customer_business_impact_mode": 75000.0,
                "customer_business_impact_max": 150000.0,
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
    iterations: Annotated[
        int,
        Field(
            default=10000,
            ge=100,
            le=100000,
            description="Number of Monte Carlo simulation trials (between 100 and 100,000)",
            examples=[10000],
        ),
    ]
    seed: Annotated[
        Optional[int],
        Field(
            default=None,
            description="Optional random seed for reproducible testing and deterministic auditing",
            examples=[42],
        ),
    ]
    currency: Annotated[
        str,
        Field(
            default="INR",
            min_length=1,
            description="Currency code for financial simulation reporting",
            examples=["INR"],
        ),
    ]

    # --- 1. Annual Event Frequency Uncertainty ---
    frequency_min: Annotated[
        float,
        Field(ge=0.0, description="Minimum annual event frequency bound (events/yr)", examples=[0.20]),
    ]
    frequency_mode: Annotated[
        float,
        Field(ge=0.0, description="Most likely (mode) annual event frequency (events/yr)", examples=[0.40]),
    ]
    frequency_max: Annotated[
        float,
        Field(ge=0.0, description="Maximum annual event frequency bound (events/yr)", examples=[0.80]),
    ]

    # --- 2. Downtime Hours Uncertainty ---
    downtime_hours_min: Annotated[
        float,
        Field(ge=0.0, description="Minimum estimated outage duration in hours", examples=[4.0]),
    ]
    downtime_hours_mode: Annotated[
        float,
        Field(ge=0.0, description="Most likely (mode) outage duration in hours", examples=[8.0]),
    ]
    downtime_hours_max: Annotated[
        float,
        Field(ge=0.0, description="Maximum estimated outage duration in hours", examples=[24.0]),
    ]

    # --- 3. Revenue Loss Per Hour Uncertainty ---
    revenue_loss_per_hour_min: Annotated[
        float,
        Field(ge=0.0, description="Minimum hourly revenue impact rate", examples=[30000.0]),
    ]
    revenue_loss_per_hour_mode: Annotated[
        float,
        Field(ge=0.0, description="Most likely (mode) hourly revenue impact rate", examples=[50000.0]),
    ]
    revenue_loss_per_hour_max: Annotated[
        float,
        Field(ge=0.0, description="Maximum hourly revenue impact rate", examples=[75000.0]),
    ]

    # --- 4. Incident Response & Forensics Cost Uncertainty ---
    incident_response_cost_min: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Minimum incident response & forensics cost", examples=[50000.0]),
    ]
    incident_response_cost_mode: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Most likely incident response & forensics cost", examples=[100000.0]),
    ]
    incident_response_cost_max: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Maximum incident response & forensics cost", examples=[180000.0]),
    ]

    # --- 5. Recovery & Rebuild Cost Uncertainty ---
    recovery_cost_min: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Minimum system recovery & data reconstruction cost", examples=[100000.0]),
    ]
    recovery_cost_mode: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Most likely system recovery & data reconstruction cost", examples=[200000.0]),
    ]
    recovery_cost_max: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Maximum system recovery & data reconstruction cost", examples=[350000.0]),
    ]

    # --- 6. Regulatory & Legal Liability Cost Uncertainty ---
    regulatory_legal_cost_min: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Minimum regulatory penalty and legal cost", examples=[20000.0]),
    ]
    regulatory_legal_cost_mode: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Most likely regulatory penalty and legal cost", examples=[50000.0]),
    ]
    regulatory_legal_cost_max: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Maximum regulatory penalty and legal cost", examples=[120000.0]),
    ]

    # --- 7. Customer & Business Impact Cost Uncertainty ---
    customer_business_impact_min: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Minimum customer SLA & reputation impact cost", examples=[30000.0]),
    ]
    customer_business_impact_mode: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Most likely customer SLA & reputation impact cost", examples=[75000.0]),
    ]
    customer_business_impact_max: Annotated[
        float,
        Field(default=0.0, ge=0.0, description="Maximum customer SLA & reputation impact cost", examples=[150000.0]),
    ]

    @model_validator(mode="after")
    def validate_triangular_bounds(self) -> "MonteCarloInput":
        """Ensure min <= mode <= max for all triangular distribution parameters."""
        triplets = [
            ("frequency", self.frequency_min, self.frequency_mode, self.frequency_max),
            ("downtime_hours", self.downtime_hours_min, self.downtime_hours_mode, self.downtime_hours_max),
            ("revenue_loss_per_hour", self.revenue_loss_per_hour_min, self.revenue_loss_per_hour_mode, self.revenue_loss_per_hour_max),
            ("incident_response_cost", self.incident_response_cost_min, self.incident_response_cost_mode, self.incident_response_cost_max),
            ("recovery_cost", self.recovery_cost_min, self.recovery_cost_mode, self.recovery_cost_max),
            ("regulatory_legal_cost", self.regulatory_legal_cost_min, self.regulatory_legal_cost_mode, self.regulatory_legal_cost_max),
            ("customer_business_impact", self.customer_business_impact_min, self.customer_business_impact_mode, self.customer_business_impact_max),
        ]

        for name, min_val, mode_val, max_val in triplets:
            if not (min_val <= mode_val <= max_val):
                raise ValueError(
                    f"Invalid distribution range for '{name}': Expected min ({min_val}) <= mode ({mode_val}) <= max ({max_val})"
                )

        return self


class SimulateFromCRQRequest(BaseModel):
    """Bridge input contract allowing direct simulation from DEV 1's Financial CRQ outputs.

    Automatically applies configurable uncertainty spread multipliers around DEV 1's
    deterministic baseline values (e.g. min = 0.5x, max = 2.0x).
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    crq_input: FinancialCRQInput = Field(
        description="Validated Financial CRQ input from DEV 1"
    )
    iterations: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Number of simulation iterations"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Optional random seed for reproducibility"
    )
    frequency_spread_min: float = Field(
        default=0.50,
        ge=0.01,
        le=1.0,
        description="Lower bound multiplier for frequency (mode × spread_min)"
    )
    frequency_spread_max: float = Field(
        default=2.00,
        ge=1.0,
        description="Upper bound multiplier for frequency (mode × spread_max)"
    )
    cost_spread_min: float = Field(
        default=0.50,
        ge=0.01,
        le=1.0,
        description="Lower bound multiplier for costs and downtime (mode × spread_min)"
    )
    cost_spread_max: float = Field(
        default=2.00,
        ge=1.0,
        description="Upper bound multiplier for costs and downtime (mode × spread_max)"
    )


class HistogramBin(BaseModel):
    """Compact histogram bin representation for rendering executive charts in the frontend."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lower_bound": 0.0,
                "upper_bound": 250000.0,
                "count": 1200,
                "percentage": 12.0,
            }
        }
    )

    lower_bound: float = Field(description="Lower limit of loss bin")
    upper_bound: float = Field(description="Upper limit of loss bin")
    count: int = Field(description="Number of simulation samples falling within this interval")
    percentage: float = Field(description="Percentage of total simulations in this bin (%)")


class MonteCarloResult(BaseModel):
    """Complete output contract of the Monte Carlo Cyber Risk Simulation Layer."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "AST-001",
                "cve_id": "CVE-001",
                "iterations": 10000,
                "mean_annual_loss": 570000.0,
                "p50": 490000.0,
                "p75": 680000.0,
                "p90": 920000.0,
                "p95": 1140000.0,
                "p99": 1530000.0,
                "min_loss": 80000.0,
                "max_loss": 3100000.0,
                "currency": "INR",
                "model_version": "MC-MVP-1.0",
                "distribution": "triangular",
                "simulation_assumptions": {
                    "frequency_distribution": "triangular",
                    "loss_distribution": "component-wise triangular",
                    "iterations": 10000,
                    "seed": 42,
                },
                "histogram": [
                    {
                        "lower_bound": 80000.0,
                        "upper_bound": 281333.33,
                        "count": 1420,
                        "percentage": 14.2,
                    }
                ],
                "explanation": [
                    "Executed 10,000 Monte Carlo stochastic trials using component-wise triangular distributions.",
                    "Expected Mean Annual Loss: ₹570,000.00",
                    "Median Annual Loss (P50): ₹490,000.00 (50% probability that annual loss is below this amount)",
                    "Tail Risk Value at Risk (P90): ₹920,000.00 (10% chance of exceeding this amount)",
                    "Extreme Tail Risk (P95): ₹1,140,000.00",
                    "Maximum Tail Exposure (P99): ₹1,530,000.00 (1-in-100 year loss event estimate)",
                ],
            }
        }
    )

    asset_id: str = Field(description="Target asset identifier")
    cve_id: Optional[str] = Field(default=None, description="Target CVE identifier")
    iterations: int = Field(description="Number of stochastic simulation iterations executed")

    # Statistical Distribution Metrics
    mean_annual_loss: float = Field(
        description="Average simulated annual loss across all iterations"
    )
    p50: float = Field(description="50th Percentile (Median) Annual Loss")
    p75: float = Field(description="75th Percentile Annual Loss")
    p90: float = Field(description="90th Percentile Annual Loss (Value at Risk / 1-in-10 year)")
    p95: float = Field(description="95th Percentile Annual Loss (Value at Risk / 1-in-20 year)")
    p99: float = Field(description="99th Percentile Annual Loss (Value at Risk / 1-in-100 year)")
    min_loss: float = Field(description="Minimum simulated annual loss observed")
    max_loss: float = Field(description="Maximum simulated annual loss observed")
    currency: str = Field(default="INR", description="Reporting currency")

    # Governance & Metadata
    model_version: str = Field(
        default="MC-MVP-1.0",
        description="Monte Carlo model version identifier"
    )
    distribution: str = Field(
        default="triangular",
        description="Underlying distribution family applied to variables"
    )
    simulation_assumptions: Dict[str, Any] = Field(
        description="Transparent simulation parameters, distributions, and random seed info"
    )
    histogram: List[HistogramBin] = Field(
        description="Histogram intervals and distribution counts for frontend visual analytics"
    )
    explanation: List[str] = Field(
        description="Deterministic executive explainability breakdown of percentile metrics"
    )


class MonteCarloHealthResponse(BaseModel):
    """Health check response schema for Monte Carlo module."""

    status: str = Field(default="ok", examples=["ok"])
    module: str = Field(default="monte-carlo", examples=["monte-carlo"])
    model_version: str = Field(default="MC-MVP-1.0", examples=["MC-MVP-1.0"])
