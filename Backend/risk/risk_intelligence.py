"""Cyber Risk Intelligence Engine (Phase 4)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Combines monetary cyber risk exposure with organizational risk appetite to compute
cyber risk debt and governance compliance status.

Functional Model:
- risk_debt = max(current_exposure - risk_appetite, 0.0)
- WITHIN_APPETITE: current_exposure < risk_appetite
- AT_APPETITE: current_exposure == risk_appetite
- ABOVE_APPETITE: current_exposure > risk_appetite
- NOT_CONFIGURED: appetite is null or no exposure exists
"""

from typing import Optional
from risk.schemas import (
    RiskAppetiteStatus,
    RiskIntelligenceResponse,
)
from risk.storage import AssessmentStorage


def calculate_risk_intelligence(
    current_exposure: Optional[float],
    risk_appetite: Optional[float],
) -> RiskIntelligenceResponse:
    """Pure, deterministic calculation of cyber risk debt and appetite status.

    Args:
        current_exposure: Aggregate Expected Annual Loss (EAL) in INR from current snapshot, or None.
        risk_appetite: Configured maximum acceptable cyber risk exposure in INR, or None.

    Returns:
        RiskIntelligenceResponse: Structured intelligence response with debt and compliance status.
    """
    has_exposure = current_exposure is not None
    has_risk_appetite = risk_appetite is not None

    if not has_exposure or not has_risk_appetite:
        return RiskIntelligenceResponse(
            current_exposure=round(current_exposure, 2) if current_exposure is not None else None,
            risk_appetite=round(risk_appetite, 2) if risk_appetite is not None else None,
            risk_debt=None,
            status=RiskAppetiteStatus.NOT_CONFIGURED,
            has_exposure=has_exposure,
            has_risk_appetite=has_risk_appetite,
        )

    exposure_val = round(current_exposure, 2)
    appetite_val = round(risk_appetite, 2)

    debt = round(max(exposure_val - appetite_val, 0.0), 2)

    if exposure_val < appetite_val:
        status = RiskAppetiteStatus.WITHIN_APPETITE
    elif exposure_val == appetite_val:
        status = RiskAppetiteStatus.AT_APPETITE
    else:
        status = RiskAppetiteStatus.ABOVE_APPETITE

    return RiskIntelligenceResponse(
        current_exposure=exposure_val,
        risk_appetite=appetite_val,
        risk_debt=debt,
        status=status,
        has_exposure=True,
        has_risk_appetite=True,
    )


def get_risk_intelligence(storage: AssessmentStorage) -> RiskIntelligenceResponse:
    """Retrieve the latest risk snapshot and current appetite from storage and compute intelligence.

    Args:
        storage: AssessmentStorage instance

    Returns:
        RiskIntelligenceResponse: Current executive risk intelligence state
    """
    latest_snapshot = storage.get_latest_snapshot()
    current_exposure = (
        float(latest_snapshot["total_exposure"]) if latest_snapshot is not None else None
    )
    current_appetite = storage.get_current_risk_appetite()
    return calculate_risk_intelligence(
        current_exposure=current_exposure,
        risk_appetite=current_appetite,
    )
