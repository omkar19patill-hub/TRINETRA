"""Risk Engine Constants & Model Configuration

TRINETRA - SIH 2026

NOTE ON PROTOTYPE ASSUMPTIONS:
The scoring weights, impact mappings, and risk-level thresholds defined in this
module are PROTOTYPE ASSUMPTIONS specifically formulated for the Smart India Hackathon
(SIH) 2026 demonstration of the TRINETRA platform. They are NOT universal cybersecurity
standards. In future production iterations, these parameters may be calibrated using
empirical loss distributions, historical incident telemetry, or custom organizational
risk appetite models.
"""

from typing import Final

# ---------------------------------------------------------------------------
# Model Metadata
# ---------------------------------------------------------------------------
MODEL_VERSION: Final[str] = "risk-model-v1"
MODEL_TYPE: Final[str] = "deterministic"

# ---------------------------------------------------------------------------
# Likelihood Calculation Weights
# ---------------------------------------------------------------------------
# Formula:
# Likelihood = (0.25 * CVSS_normalized)
#            + (0.40 * EPSS)
#            + (0.20 * KEV_signal)
#            + (0.15 * Exposure_signal)
# Sum of weights: 0.25 + 0.40 + 0.20 + 0.15 = 1.00
CVSS_WEIGHT: Final[float] = 0.25
EPSS_WEIGHT: Final[float] = 0.40
KEV_WEIGHT: Final[float] = 0.20
EXPOSURE_WEIGHT: Final[float] = 0.15

# Verification check to ensure likelihood weights always sum to 1.0
assert abs((CVSS_WEIGHT + EPSS_WEIGHT + KEV_WEIGHT + EXPOSURE_WEIGHT) - 1.0) < 1e-6, (
    "Likelihood weights must sum to 1.00"
)

# ---------------------------------------------------------------------------
# Asset Business Criticality Impact Mapping
# ---------------------------------------------------------------------------
# Maps business criticality tiers to deterministic impact multipliers [0.0 - 1.0].
# Financial loss (EAL / Monte Carlo) will integrate on top of this in later phases.
CRITICALITY_IMPACT: Final[dict[str, float]] = {
    "Critical": 1.00,
    "High": 0.75,
    "Medium": 0.50,
    "Low": 0.25,
}

# ---------------------------------------------------------------------------
# Risk Score Thresholds & Levels
# ---------------------------------------------------------------------------
# Scale: 0 - 100
# 0  - 24.99... -> LOW
# 25 - 49.99... -> MEDIUM
# 50 - 74.99... -> HIGH
# 75 - 100.0    -> CRITICAL
RISK_LEVEL_THRESHOLDS: Final[list[tuple[float, str]]] = [
    (75.0, "CRITICAL"),
    (50.0, "HIGH"),
    (25.0, "MEDIUM"),
    (0.0, "LOW"),
]

# ---------------------------------------------------------------------------
# Risk Driver Generation Thresholds
# ---------------------------------------------------------------------------
# Thresholds that trigger qualitative risk driver tags for explainability
CVSS_DRIVER_THRESHOLD: Final[float] = 9.0
EPSS_DRIVER_THRESHOLD: Final[float] = 0.70

# ---------------------------------------------------------------------------
# Bounds & Precision
# ---------------------------------------------------------------------------
MIN_RISK_SCORE: Final[float] = 0.0
MAX_RISK_SCORE: Final[float] = 100.0
SCORE_DECIMAL_PLACES: Final[int] = 2
CALCULATION_DECIMAL_PLACES: Final[int] = 4
