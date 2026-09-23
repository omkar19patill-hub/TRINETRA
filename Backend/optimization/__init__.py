"""TRINETRA Cybersecurity Investment Optimization Module

SIH 2026 - Problem ID: SIH26105
"""

OPTIMIZATION_MODEL_VERSION = "OPT-DET-1.0"

from .evaluator import FactorEvaluationResult, evaluate_controls_portfolio
from .optimizer import run_optimization
from .routes import router
from .schemas import (
    BeforeAfterRequest,
    BeforeAfterResponse,
    DeltaMetrics,
    OptimizationRunRequest,
    OptimizationRunResponse,
    RiskSnapshot,
)

__all__ = [
    "OPTIMIZATION_MODEL_VERSION",
    "run_optimization",
    "evaluate_controls_portfolio",
    "FactorEvaluationResult",
    "OptimizationRunRequest",
    "OptimizationRunResponse",
    "BeforeAfterRequest",
    "BeforeAfterResponse",
    "RiskSnapshot",
    "DeltaMetrics",
    "router",
]
