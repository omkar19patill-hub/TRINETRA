"""Core Monte Carlo Simulation Engine

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Stochastic Uncertainty Modeling & Distribution Metrics

Pure Python simulation engine executing Monte Carlo trials using component-wise
triangular distributions for cyber risk event frequency and loss magnitudes.
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from .schemas import (
    MonteCarloInput,
    MonteCarloResult,
    HistogramBin,
    SimulateFromCRQRequest,
)
from financial_crq.schemas import FinancialCRQInput
from financial_crq.engine import format_currency_amount

MONTE_CARLO_MODEL_VERSION: str = "MC-MVP-1.0"
DEFAULT_HISTOGRAM_BINS: int = 15


def compute_percentiles(
    losses: List[float],
    percentile_ranks: Optional[List[float]] = None,
) -> Dict[str, float]:
    """Calculate statistical percentiles using robust linear interpolation.

    Args:
        losses: List of sampled annual losses from simulation
        percentile_ranks: Percentile levels to compute [0 - 100] (default: [50, 75, 90, 95, 99])

    Returns:
        Dictionary mapping percentile names ('p50', 'p75', etc.) to rounded values.
    """
    if not losses:
        raise ValueError("Cannot calculate percentiles for an empty sample list.")

    if percentile_ranks is None:
        percentile_ranks = [50.0, 75.0, 90.0, 95.0, 99.0]

    np_losses = np.array(losses, dtype=np.float64)
    computed = np.percentile(np_losses, percentile_ranks)

    result = {}
    for rank, val in zip(percentile_ranks, computed):
        key = f"p{int(rank)}"
        result[key] = round(float(val), 2)

    return result


def build_histogram(
    losses: List[float],
    num_bins: int = DEFAULT_HISTOGRAM_BINS,
) -> List[HistogramBin]:
    """Partition simulation results into compact histogram intervals for frontend visualization.

    Args:
        losses: List of sampled annual losses
        num_bins: Target number of histogram bins (default: 15)

    Returns:
        List of HistogramBin models with interval ranges, counts, and percentages.
    """
    if not losses:
        return []

    np_losses = np.array(losses, dtype=np.float64)
    total_samples = len(losses)
    min_val = float(np.min(np_losses))
    max_val = float(np.max(np_losses))

    # Single point edge case
    if math.isclose(min_val, max_val, rel_tol=1e-9):
        return [
            HistogramBin(
                lower_bound=round(min_val, 2),
                upper_bound=round(max_val, 2),
                count=total_samples,
                percentage=100.0,
            )
        ]

    counts, bin_edges = np.histogram(np_losses, bins=num_bins)

    bins: List[HistogramBin] = []
    for i in range(len(counts)):
        lower = round(float(bin_edges[i]), 2)
        upper = round(float(bin_edges[i + 1]), 2)
        count = int(counts[i])
        pct = round((count / total_samples) * 100.0, 2)
        bins.append(
            HistogramBin(
                lower_bound=lower,
                upper_bound=upper,
                count=count,
                percentage=pct,
            )
        )

    return bins


def generate_monte_carlo_explanation(
    iterations: int,
    mean_loss: float,
    percentiles: Dict[str, float],
    min_loss: float,
    max_loss: float,
    currency: str = "INR",
) -> List[str]:
    """Construct transparent explainability statements describing simulation findings."""
    fmt_mean = format_currency_amount(mean_loss, currency)
    fmt_p50 = format_currency_amount(percentiles.get("p50", 0.0), currency)
    fmt_p75 = format_currency_amount(percentiles.get("p75", 0.0), currency)
    fmt_p90 = format_currency_amount(percentiles.get("p90", 0.0), currency)
    fmt_p95 = format_currency_amount(percentiles.get("p95", 0.0), currency)
    fmt_p99 = format_currency_amount(percentiles.get("p99", 0.0), currency)
    fmt_min = format_currency_amount(min_loss, currency)
    fmt_max = format_currency_amount(max_loss, currency)

    return [
        (
            f"Executed {iterations:,} Monte Carlo stochastic iterations using component-wise "
            "triangular probability distributions."
        ),
        f"Mean Expected Annual Loss: {fmt_mean} across simulated scenarios.",
        f"Median Annual Loss (P50): {fmt_p50} (50% probability annual loss is below this threshold).",
        f"75th Percentile Exposure (P75): {fmt_p75}.",
        f"90th Percentile Value at Risk (P90): {fmt_p90} (1-in-10 year loss expectation).",
        f"95th Percentile Severe Risk (P95): {fmt_p95} (1-in-20 year loss expectation).",
        f"99th Percentile Worst-Case Tail Exposure (P99): {fmt_p99} (1-in-100 year catastrophic loss scenario).",
        f"Observed simulated loss range: {fmt_min} to {fmt_max}.",
    ]


def run_simulation(
    input_data: Union[MonteCarloInput, Dict[str, Any]],
) -> MonteCarloResult:
    """Execute end-to-end Monte Carlo simulation for cyber risk quantification.

    Sampling Process per Iteration:
        1. Sample Annual Event Frequency ~ Triangular(min, mode, max)
        2. Sample Downtime Duration (hrs) ~ Triangular(min, mode, max)
        3. Sample Revenue Loss Rate (₹/hr) ~ Triangular(min, mode, max)
        4. Compute Sampled Downtime Loss = downtime_hours × revenue_loss_per_hour
        5. Sample Forensics/IR, Recovery, Regulatory/Legal, and Customer Impact Costs
        6. Compute Total Event Loss Magnitude = sum(all sampled loss components)
        7. Compute Annual Loss = sampled_event_frequency × sampled_loss_magnitude
        8. Aggregate distribution across all iterations to derive percentiles and histogram bins

    Args:
        input_data: Validated MonteCarloInput instance or equivalent dictionary

    Returns:
        MonteCarloResult containing all distribution percentiles, histogram bins, and metadata.
    """
    if isinstance(input_data, dict):
        validated_input = MonteCarloInput(**input_data)
    elif isinstance(input_data, MonteCarloInput):
        validated_input = input_data
    else:
        raise TypeError(
            f"Expected MonteCarloInput or dict, got {type(input_data).__name__}"
        )

    # Initialize random number generator (seedable for deterministic testing)
    rng = random.Random(validated_input.seed) if validated_input.seed is not None else random.Random()

    iterations = validated_input.iterations
    annual_losses: List[float] = [0.0] * iterations

    # Cache distribution parameter bounds for fast iteration loop
    f_min, f_mode, f_max = (
        validated_input.frequency_min,
        validated_input.frequency_mode,
        validated_input.frequency_max,
    )
    dt_min, dt_mode, dt_max = (
        validated_input.downtime_hours_min,
        validated_input.downtime_hours_mode,
        validated_input.downtime_hours_max,
    )
    rev_min, rev_mode, rev_max = (
        validated_input.revenue_loss_per_hour_min,
        validated_input.revenue_loss_per_hour_mode,
        validated_input.revenue_loss_per_hour_max,
    )
    ir_min, ir_mode, ir_max = (
        validated_input.incident_response_cost_min,
        validated_input.incident_response_cost_mode,
        validated_input.incident_response_cost_max,
    )
    rec_min, rec_mode, rec_max = (
        validated_input.recovery_cost_min,
        validated_input.recovery_cost_mode,
        validated_input.recovery_cost_max,
    )
    reg_min, reg_mode, reg_max = (
        validated_input.regulatory_legal_cost_min,
        validated_input.regulatory_legal_cost_mode,
        validated_input.regulatory_legal_cost_max,
    )
    cust_min, cust_mode, cust_max = (
        validated_input.customer_business_impact_min,
        validated_input.customer_business_impact_mode,
        validated_input.customer_business_impact_max,
    )

    # Core simulation loop
    for i in range(iterations):
        # 1. Event frequency
        freq_sample = rng.triangular(f_min, f_max, f_mode)

        # 2. Downtime duration and revenue impact
        dt_sample = rng.triangular(dt_min, dt_max, dt_mode)
        rev_sample = rng.triangular(rev_min, rev_max, rev_mode)
        dt_loss_sample = dt_sample * rev_sample

        # 3. Direct response, recovery, legal, and business impact costs
        ir_sample = rng.triangular(ir_min, ir_max, ir_mode)
        rec_sample = rng.triangular(rec_min, rec_max, rec_mode)
        reg_sample = rng.triangular(reg_min, reg_max, reg_mode)
        cust_sample = rng.triangular(cust_min, cust_max, cust_mode)

        # 4. Total event loss magnitude
        loss_mag_sample = (
            dt_loss_sample
            + ir_sample
            + rec_sample
            + reg_sample
            + cust_sample
        )

        # 5. Annual loss = frequency × loss magnitude
        annual_losses[i] = freq_sample * loss_mag_sample

    # Compute Statistical Metrics
    mean_annual_loss = round(float(np.mean(annual_losses)), 2)
    percentiles = compute_percentiles(annual_losses, [50.0, 75.0, 90.0, 95.0, 99.0])
    min_loss = round(float(np.min(annual_losses)), 2)
    max_loss = round(float(np.max(annual_losses)), 2)

    # Build Histogram Bins
    histogram = build_histogram(annual_losses, num_bins=DEFAULT_HISTOGRAM_BINS)

    # Generate Explainability Statements
    explanation = generate_monte_carlo_explanation(
        iterations=iterations,
        mean_loss=mean_annual_loss,
        percentiles=percentiles,
        min_loss=min_loss,
        max_loss=max_loss,
        currency=validated_input.currency,
    )

    simulation_assumptions = {
        "frequency_distribution": "triangular",
        "loss_distribution": "component-wise triangular",
        "iterations": iterations,
        "seed": validated_input.seed,
        "model_type": "stochastic",
        "note": "Prototype Monte Carlo model under triangular distribution assumptions. Values represent modeled stochastic estimates.",
    }

    return MonteCarloResult(
        asset_id=validated_input.asset_id,
        cve_id=validated_input.cve_id,
        iterations=iterations,
        mean_annual_loss=mean_annual_loss,
        p50=percentiles["p50"],
        p75=percentiles["p75"],
        p90=percentiles["p90"],
        p95=percentiles["p95"],
        p99=percentiles["p99"],
        min_loss=min_loss,
        max_loss=max_loss,
        currency=validated_input.currency,
        model_version=MONTE_CARLO_MODEL_VERSION,
        distribution="triangular",
        simulation_assumptions=simulation_assumptions,
        histogram=histogram,
        explanation=explanation,
    )


def build_monte_carlo_input_from_crq(
    crq_input: FinancialCRQInput,
    iterations: int = 10000,
    seed: Optional[int] = None,
    frequency_spread_min: float = 0.50,
    frequency_spread_max: float = 2.00,
    cost_spread_min: float = 0.50,
    cost_spread_max: float = 2.00,
) -> MonteCarloInput:
    """Transform DEV 1's FinancialCRQInput into MonteCarloInput by applying spread factors.

    Args:
        crq_input: FinancialCRQInput instance from DEV 1
        iterations: Number of simulation iterations (default: 10,000)
        seed: Optional RNG seed
        frequency_spread_min: Lower multiplier for annual event frequency (default: 0.5)
        frequency_spread_max: Upper multiplier for annual event frequency (default: 2.0)
        cost_spread_min: Lower multiplier for downtime and cost components (default: 0.5)
        cost_spread_max: Upper multiplier for downtime and cost components (default: 2.0)

    Returns:
        Validated MonteCarloInput populated with (min, mode, max) triplets.
    """
    freq_mode = crq_input.baseline_annual_frequency * crq_input.likelihood
    freq_min = freq_mode * frequency_spread_min
    freq_max = freq_mode * frequency_spread_max

    def get_bounds(mode_val: float) -> Tuple[float, float, float]:
        if mode_val == 0.0:
            return 0.0, 0.0, 0.0
        return (
            round(mode_val * cost_spread_min, 2),
            round(mode_val, 2),
            round(mode_val * cost_spread_max, 2),
        )

    dt_min, dt_mode, dt_max = get_bounds(crq_input.downtime_hours)
    rev_min, rev_mode, rev_max = get_bounds(crq_input.revenue_loss_per_hour)
    ir_min, ir_mode, ir_max = get_bounds(crq_input.incident_response_cost)
    rec_min, rec_mode, rec_max = get_bounds(crq_input.recovery_cost)
    reg_min, reg_mode, reg_max = get_bounds(crq_input.regulatory_legal_cost)
    cust_min, cust_mode, cust_max = get_bounds(crq_input.customer_business_impact)

    return MonteCarloInput(
        asset_id=crq_input.asset_id,
        cve_id=crq_input.cve_id,
        iterations=iterations,
        seed=seed,
        currency=crq_input.currency,
        frequency_min=round(freq_min, 4),
        frequency_mode=round(freq_mode, 4),
        frequency_max=round(freq_max, 4),
        downtime_hours_min=dt_min,
        downtime_hours_mode=dt_mode,
        downtime_hours_max=dt_max,
        revenue_loss_per_hour_min=rev_min,
        revenue_loss_per_hour_mode=rev_mode,
        revenue_loss_per_hour_max=rev_max,
        incident_response_cost_min=ir_min,
        incident_response_cost_mode=ir_mode,
        incident_response_cost_max=ir_max,
        recovery_cost_min=rec_min,
        recovery_cost_mode=rec_mode,
        recovery_cost_max=rec_max,
        regulatory_legal_cost_min=reg_min,
        regulatory_legal_cost_mode=reg_mode,
        regulatory_legal_cost_max=reg_max,
        customer_business_impact_min=cust_min,
        customer_business_impact_mode=cust_mode,
        customer_business_impact_max=cust_max,
    )
