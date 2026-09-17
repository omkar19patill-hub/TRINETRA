"""Financial Cyber Risk Quantification (CRQ) Package

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
"""

from .schemas import (
    FinancialCRQInput,
    FinancialCRQResult,
    LossComponents,
    MonteCarloInput,
    FinancialCRQHealthResponse,
    VALID_CRITICALITIES,
)
from .engine import (
    calculate_financial_crq,
    calculate_downtime_loss,
    calculate_loss_magnitude,
    calculate_event_frequency,
    calculate_eal,
    generate_financial_explanation,
    generate_financial_assumptions,
    from_risk_result,
    FINANCIAL_MODEL_VERSION,
    DEFAULT_BASELINE_FREQUENCY,
)

__all__ = [
    "FinancialCRQInput",
    "FinancialCRQResult",
    "LossComponents",
    "MonteCarloInput",
    "FinancialCRQHealthResponse",
    "VALID_CRITICALITIES",
    "calculate_financial_crq",
    "calculate_downtime_loss",
    "calculate_loss_magnitude",
    "calculate_event_frequency",
    "calculate_eal",
    "generate_financial_explanation",
    "generate_financial_assumptions",
    "from_risk_result",
    "FINANCIAL_MODEL_VERSION",
    "DEFAULT_BASELINE_FREQUENCY",
]
