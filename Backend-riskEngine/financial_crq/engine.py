"""Core Financial Cyber Risk Quantification (CRQ) Engine

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Pure Python financial modeling engine decoupled from FastAPI and HTTP layers.
Computes:
1. Downtime Loss = revenue_loss_per_hour × downtime_hours
2. Loss Magnitude = downtime_loss + incident_response + recovery + legal + customer_impact
3. Loss Event Frequency = baseline_annual_frequency × likelihood
4. Expected Annual Loss (EAL) = Annual Event Frequency × Loss Magnitude
5. Deterministic Explainability & Assumptions Metadata
6. Structured MonteCarloInput for downstream simulation (DEV 2)
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from .schemas import (
    FinancialCRQInput,
    FinancialCRQResult,
    LossComponents,
    MonteCarloInput,
    VALID_CRITICALITIES,
)


FINANCIAL_MODEL_VERSION: str = "CRQ-MVP-1.0"
DEFAULT_BASELINE_FREQUENCY: float = 1.0


def calculate_downtime_loss(
    revenue_loss_per_hour: float,
    downtime_hours: float,
) -> float:
    """Calculate direct financial loss incurred during operational downtime.

    Formula:
        downtime_loss = revenue_loss_per_hour × downtime_hours

    Args:
        revenue_loss_per_hour: Monetary revenue lost per hour of outage (>= 0)
        downtime_hours: Total duration of service outage in hours (>= 0)

    Returns:
        Calculated downtime loss rounded to 2 decimal places.
    """
    if revenue_loss_per_hour < 0 or downtime_hours < 0:
        raise ValueError("Revenue loss per hour and downtime hours must be non-negative.")
    return round(revenue_loss_per_hour * downtime_hours, 2)


def calculate_loss_magnitude(
    downtime_loss: float,
    incident_response_cost: float = 0.0,
    recovery_cost: float = 0.0,
    regulatory_legal_cost: float = 0.0,
    customer_business_impact: float = 0.0,
) -> LossComponents:
    """Calculate total loss magnitude per security event and individual components.

    Formula:
        total_loss_magnitude = downtime_loss
                             + incident_response_cost
                             + recovery_cost
                             + regulatory_legal_cost
                             + customer_business_impact

    Args:
        downtime_loss: Precomputed downtime loss (>= 0)
        incident_response_cost: Forensics and triage cost (>= 0)
        recovery_cost: IT recovery, data rebuild cost (>= 0)
        regulatory_legal_cost: Legal, compliance, fine cost (>= 0)
        customer_business_impact: SLA, customer compensation, churn impact (>= 0)

    Returns:
        LossComponents instance containing individual and aggregate losses.
    """
    costs = [
        downtime_loss,
        incident_response_cost,
        recovery_cost,
        regulatory_legal_cost,
        customer_business_impact,
    ]
    if any(c < 0 for c in costs):
        raise ValueError("All loss components must be non-negative.")

    total = sum(costs)
    return LossComponents(
        downtime_loss=round(downtime_loss, 2),
        incident_response_cost=round(incident_response_cost, 2),
        recovery_cost=round(recovery_cost, 2),
        regulatory_legal_cost=round(regulatory_legal_cost, 2),
        customer_business_impact=round(customer_business_impact, 2),
        total_loss_magnitude=round(total, 2),
    )


def calculate_event_frequency(
    likelihood: float,
    baseline_annual_frequency: float = DEFAULT_BASELINE_FREQUENCY,
) -> float:
    """Model annual loss event frequency from cyber risk likelihood score.

    IMPORTANT MODELING ASSUMPTION:
    The cyber risk score and likelihood are model-derived indicators synthesizing
    CVSS, EPSS, and KEV, and do not represent guaranteed attack probabilities.
    This function applies a configurable baseline frequency to model expected
    event frequency per year for the prototype. In production, baseline frequency
    must be calibrated using historical organizational incident telemetry.

    Formula:
        annual_event_frequency = baseline_annual_frequency × likelihood

    Args:
        likelihood: Exploitation likelihood score [0.0 - 1.0]
        baseline_annual_frequency: Configurable annual attack attempt baseline (>= 0)

    Returns:
        Modeled annual event frequency rounded to 4 decimal places.
    """
    if likelihood < 0 or likelihood > 1.0:
        raise ValueError("Likelihood must be between 0.0 and 1.0.")
    if baseline_annual_frequency < 0:
        raise ValueError("Baseline annual frequency must be non-negative.")

    return round(baseline_annual_frequency * likelihood, 4)


def calculate_eal(
    annual_event_frequency: float,
    total_loss_magnitude: float,
) -> float:
    """Calculate Expected Annual Loss (EAL).

    Formula:
        Expected Annual Loss (EAL) = Annual Event Frequency × Total Loss Magnitude

    NOTE:
    EAL is a modeled mathematical expectation under stated assumptions,
    not a deterministic prediction or guarantee.

    Args:
        annual_event_frequency: Modeled events per year (>= 0)
        total_loss_magnitude: Total modeled loss per event (>= 0)

    Returns:
        Expected Annual Loss rounded to 2 decimal places.
    """
    if annual_event_frequency < 0 or total_loss_magnitude < 0:
        raise ValueError("Event frequency and loss magnitude must be non-negative.")

    return round(annual_event_frequency * total_loss_magnitude, 2)


def format_currency_amount(amount: float, currency: str = "INR") -> str:
    """Format monetary values with appropriate currency symbols and thousands separators."""
    symbol = "₹" if currency.upper() == "INR" else f"{currency.upper()} "
    return f"{symbol}{amount:,.2f}"


def generate_financial_explanation(
    likelihood: float,
    baseline_annual_frequency: float,
    annual_event_frequency: float,
    loss_components: LossComponents,
    eal: float,
    currency: str = "INR",
    downtime_hours: float = 0.0,
    revenue_loss_per_hour: float = 0.0,
) -> List[str]:
    """Generate deterministic, human-readable explainability statements for board reporting."""
    fmt_dt = format_currency_amount(loss_components.downtime_loss, currency)
    fmt_ir = format_currency_amount(loss_components.incident_response_cost, currency)
    fmt_rec = format_currency_amount(loss_components.recovery_cost, currency)
    fmt_reg = format_currency_amount(loss_components.regulatory_legal_cost, currency)
    fmt_cust = format_currency_amount(loss_components.customer_business_impact, currency)
    fmt_tot = format_currency_amount(loss_components.total_loss_magnitude, currency)
    fmt_eal = format_currency_amount(eal, currency)
    fmt_rate = format_currency_amount(revenue_loss_per_hour, currency)

    explanation = [
        (
            f"Modeled event frequency: {annual_event_frequency:.2f} events/year "
            f"(Likelihood: {likelihood:.2f} × Baseline frequency: {baseline_annual_frequency:.2f} events/yr)"
        ),
        f"Downtime loss: {fmt_dt} ({downtime_hours:.2f} hrs × {fmt_rate}/hr)",
    ]

    if loss_components.incident_response_cost > 0:
        explanation.append(f"Incident response & forensics cost: {fmt_ir}")
    if loss_components.recovery_cost > 0:
        explanation.append(f"System recovery & data reconstruction cost: {fmt_rec}")
    if loss_components.regulatory_legal_cost > 0:
        explanation.append(f"Regulatory penalties & legal defense cost: {fmt_reg}")
    if loss_components.customer_business_impact > 0:
        explanation.append(f"Customer compensation & SLA penalty impact: {fmt_cust}")

    explanation.append(f"Total modeled loss per event (Loss Magnitude): {fmt_tot}")
    explanation.append(
        f"Expected Annual Loss (EAL): {fmt_eal} ({annual_event_frequency:.2f} events/yr × {fmt_tot}/event)"
    )

    return explanation


def generate_financial_assumptions(
    baseline_annual_frequency: float,
    likelihood: float,
    eal: float,
    currency: str = "INR",
) -> List[str]:
    """Generate explicit governance assumptions describing model constraints."""
    fmt_eal = format_currency_amount(eal, currency)
    return [
        (
            f"Baseline annual frequency ({baseline_annual_frequency:.2f} events/yr) "
            "is a configurable prototype modeling assumption."
        ),
        (
            f"Likelihood ({likelihood:.4f}) is derived from technical CVSS/EPSS/KEV indicators "
            "and represents a model score, not an empirical attack probability."
        ),
        "Financial cost parameters and downtime durations are organization-provided estimates or synthetic demonstration values.",
        (
            f"Expected Annual Loss (EAL = {fmt_eal}) represents a modeled statistical expectation "
            "under current assumptions, not a guaranteed loss forecast."
        ),
    ]


def calculate_financial_crq(
    input_data: Union[FinancialCRQInput, Dict[str, Any]],
) -> FinancialCRQResult:
    """Orchestrate the end-to-end Financial Cyber Risk Quantification calculation.

    Workflow:
        1. Validate inputs against FinancialCRQInput schema
        2. Calculate direct downtime loss = revenue_loss_per_hour × downtime_hours
        3. Aggregate all cost components to determine Total Loss Magnitude
        4. Model Loss Event Frequency = baseline_annual_frequency × likelihood
        5. Compute Expected Annual Loss (EAL) = Annual Event Frequency × Total Loss Magnitude
        6. Generate transparent, deterministic explainability statements
        7. Assemble structured MonteCarloInput for downstream simulation (DEV 2)
        8. Package complete FinancialCRQResult

    Args:
        input_data: Validated FinancialCRQInput instance or raw dictionary

    Returns:
        FinancialCRQResult populated with all financial dimensions and DEV 2 payload.
    """
    if isinstance(input_data, dict):
        validated_input = FinancialCRQInput(**input_data)
    elif isinstance(input_data, FinancialCRQInput):
        validated_input = input_data
    else:
        raise TypeError(
            f"Expected FinancialCRQInput or dict, got {type(input_data).__name__}"
        )

    # 1. Downtime Loss
    downtime_loss = calculate_downtime_loss(
        revenue_loss_per_hour=validated_input.revenue_loss_per_hour,
        downtime_hours=validated_input.downtime_hours,
    )

    # 2. Loss Magnitude Components
    loss_components = calculate_loss_magnitude(
        downtime_loss=downtime_loss,
        incident_response_cost=validated_input.incident_response_cost,
        recovery_cost=validated_input.recovery_cost,
        regulatory_legal_cost=validated_input.regulatory_legal_cost,
        customer_business_impact=validated_input.customer_business_impact,
    )

    # 3. Loss Event Frequency
    annual_event_frequency = calculate_event_frequency(
        likelihood=validated_input.likelihood,
        baseline_annual_frequency=validated_input.baseline_annual_frequency,
    )

    # 4. Expected Annual Loss (EAL)
    expected_annual_loss = calculate_eal(
        annual_event_frequency=annual_event_frequency,
        total_loss_magnitude=loss_components.total_loss_magnitude,
    )

    # 5. Explanations & Assumptions
    explanation = generate_financial_explanation(
        likelihood=validated_input.likelihood,
        baseline_annual_frequency=validated_input.baseline_annual_frequency,
        annual_event_frequency=annual_event_frequency,
        loss_components=loss_components,
        eal=expected_annual_loss,
        currency=validated_input.currency,
        downtime_hours=validated_input.downtime_hours,
        revenue_loss_per_hour=validated_input.revenue_loss_per_hour,
    )

    assumptions = generate_financial_assumptions(
        baseline_annual_frequency=validated_input.baseline_annual_frequency,
        likelihood=validated_input.likelihood,
        eal=expected_annual_loss,
        currency=validated_input.currency,
    )

    # 6. DEV 2 Monte Carlo Input Contract
    monte_carlo_input = MonteCarloInput(
        asset_id=validated_input.asset_id,
        cve_id=validated_input.cve_id,
        annual_frequency_assumption=annual_event_frequency,
        downtime_hours=validated_input.downtime_hours,
        revenue_loss_per_hour=validated_input.revenue_loss_per_hour,
        incident_response_cost=validated_input.incident_response_cost,
        recovery_cost=validated_input.recovery_cost,
        regulatory_legal_cost=validated_input.regulatory_legal_cost,
        customer_business_impact=validated_input.customer_business_impact,
        loss_magnitude=loss_components.total_loss_magnitude,
        baseline_annual_frequency=validated_input.baseline_annual_frequency,
        likelihood=validated_input.likelihood,
        currency=validated_input.currency,
    )

    # 7. Complete Financial CRQ Result
    return FinancialCRQResult(
        asset_id=validated_input.asset_id,
        cve_id=validated_input.cve_id,
        likelihood=validated_input.likelihood,
        baseline_annual_frequency=validated_input.baseline_annual_frequency,
        annual_event_frequency=annual_event_frequency,
        downtime_loss=loss_components.downtime_loss,
        incident_response_cost=loss_components.incident_response_cost,
        recovery_cost=loss_components.recovery_cost,
        regulatory_legal_cost=loss_components.regulatory_legal_cost,
        customer_business_impact=loss_components.customer_business_impact,
        total_loss_magnitude=loss_components.total_loss_magnitude,
        expected_annual_loss=expected_annual_loss,
        currency=validated_input.currency,
        assumptions=assumptions,
        model_version=FINANCIAL_MODEL_VERSION,
        explanation=explanation,
        monte_carlo_input=monte_carlo_input,
    )


def from_risk_result(
    risk_result: Any,
    financial_params: Dict[str, Any],
) -> FinancialCRQInput:
    """Bridge helper to construct FinancialCRQInput from a Cyber Risk Engine result.

    Extracts asset_id, cve_id, likelihood, risk_score, and criticality from
    a RiskCalculationResponse or RiskResult, and merges them with financial parameters.

    Args:
        risk_result: RiskCalculationResponse, RiskResult, or compatible dictionary/object
        financial_params: Dictionary of financial parameters (revenue_loss_per_hour, downtime_hours, etc.)

    Returns:
        Validated FinancialCRQInput instance.
    """
    if isinstance(risk_result, dict):
        asset_id = risk_result.get("asset_id")
        cve_id = risk_result.get("cve_id")
        likelihood = risk_result.get("likelihood", 0.0)
        risk_score = risk_result.get("risk_score", 0.0)
        criticality = risk_result.get("criticality", "High")
    else:
        asset_id = getattr(risk_result, "asset_id", None)
        cve_id = getattr(risk_result, "cve_id", None)
        likelihood = getattr(risk_result, "likelihood", 0.0)
        risk_score = getattr(risk_result, "risk_score", 0.0)
        # Check if criticality exists on object or if we deduce from risk_level / default
        criticality = getattr(risk_result, "criticality", "High")
        if hasattr(criticality, "value"):
            criticality = criticality.value

    merged_data = {
        "asset_id": asset_id,
        "cve_id": cve_id,
        "likelihood": likelihood,
        "risk_score": risk_score,
        "criticality": criticality if criticality in VALID_CRITICALITIES else "High",
        **financial_params,
    }

    return FinancialCRQInput(**merged_data)
