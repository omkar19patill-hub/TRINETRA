"""Monte Carlo Cyber Risk Simulation Package

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Stochastic Uncertainty & Monte Carlo Simulation Layer
"""

from .schemas import (
    MonteCarloInput,
    MonteCarloResult,
    HistogramBin,
    SimulateFromCRQRequest,
    MonteCarloHealthResponse,
)
from .simulator import (
    run_simulation,
    compute_percentiles,
    build_histogram,
    build_monte_carlo_input_from_crq,
    generate_monte_carlo_explanation,
    MONTE_CARLO_MODEL_VERSION,
)

__all__ = [
    "MonteCarloInput",
    "MonteCarloResult",
    "HistogramBin",
    "SimulateFromCRQRequest",
    "MonteCarloHealthResponse",
    "run_simulation",
    "compute_percentiles",
    "build_histogram",
    "build_monte_carlo_input_from_crq",
    "generate_monte_carlo_explanation",
    "MONTE_CARLO_MODEL_VERSION",
]
