"""Risk Change Intelligence Module (Phase 3)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Compares run-over-run portfolio risk snapshots to explain how financial cyber risk,
average risk score, and asset criticality counts have changed between assessment runs.

Deterministic, zero-side-effect evaluation conforming to strict Open FAIR and
deterministic scoring boundaries.
"""

from typing import Any, Dict, Optional, Union
from risk.schemas import RiskChangeResponse, RiskSnapshotResponse
from risk.storage import AssessmentStorage


def compute_risk_change(
    current: Optional[Union[Dict[str, Any], RiskSnapshotResponse]] = None,
    previous: Optional[Union[Dict[str, Any], RiskSnapshotResponse]] = None,
) -> RiskChangeResponse:
    """Compute deterministic run-over-run risk change metrics between two snapshots.

    Explicitly handles:
    1. No previous snapshot (only current present)
    2. No history (both None)
    3. Previous exposure = 0 (avoids division by zero; percentage_change is None)
    4. Current exposure = 0
    5. Exposure increased
    6. Exposure decreased
    7. Exposure unchanged
    8. Identical snapshots

    Args:
        current: Most recent snapshot (dict or RiskSnapshotResponse) or None
        previous: Immediately preceding snapshot (dict or RiskSnapshotResponse) or None

    Returns:
        RiskChangeResponse: Structured comparison metrics and snapshot metadata
    """
    if not current:
        return RiskChangeResponse(
            has_history=False,
            has_baseline=False,
            current_snapshot=None,
            previous_snapshot=None,
            previous_exposure=None,
            current_exposure=None,
            absolute_change=None,
            percentage_change=None,
            previous_average_risk=None,
            current_average_risk=None,
            average_risk_change=None,
            previous_critical_assets=None,
            current_critical_assets=None,
            critical_assets_change=None,
            previous_high_risk_assets=None,
            current_high_risk_assets=None,
            high_risk_assets_change=None,
        )

    current_obj = (
        current if isinstance(current, RiskSnapshotResponse) else RiskSnapshotResponse(**current)
    )

    if not previous:
        return RiskChangeResponse(
            has_history=True,
            has_baseline=False,
            current_snapshot=current_obj,
            previous_snapshot=None,
            previous_exposure=None,
            current_exposure=round(current_obj.total_exposure, 2),
            absolute_change=None,
            percentage_change=None,
            previous_average_risk=None,
            current_average_risk=round(current_obj.average_risk, 2),
            average_risk_change=None,
            previous_critical_assets=None,
            current_critical_assets=current_obj.critical_assets,
            critical_assets_change=None,
            previous_high_risk_assets=None,
            current_high_risk_assets=current_obj.high_risk_assets,
            high_risk_assets_change=None,
        )

    prev_obj = (
        previous if isinstance(previous, RiskSnapshotResponse) else RiskSnapshotResponse(**previous)
    )

    # 1. Financial Exposure changes
    cur_exp = round(current_obj.total_exposure, 2)
    prev_exp = round(prev_obj.total_exposure, 2)
    absolute_change = round(cur_exp - prev_exp, 2)

    # Percentage change: guard against zero division
    if prev_exp != 0.0:
        percentage_change = round(((cur_exp - prev_exp) / prev_exp) * 100.0, 2)
    else:
        percentage_change = None

    # 2. Average Risk Score changes
    cur_avg = round(current_obj.average_risk, 2)
    prev_avg = round(prev_obj.average_risk, 2)
    avg_change = round(cur_avg - prev_avg, 2)

    # 3. Critical Assets changes
    cur_crit = current_obj.critical_assets
    prev_crit = prev_obj.critical_assets
    crit_change = cur_crit - prev_crit

    # 4. High Risk Assets changes
    cur_high = current_obj.high_risk_assets
    prev_high = prev_obj.high_risk_assets
    high_change = cur_high - prev_high

    return RiskChangeResponse(
        has_history=True,
        has_baseline=True,
        current_snapshot=current_obj,
        previous_snapshot=prev_obj,
        previous_exposure=prev_exp,
        current_exposure=cur_exp,
        absolute_change=absolute_change,
        percentage_change=percentage_change,
        previous_average_risk=prev_avg,
        current_average_risk=cur_avg,
        average_risk_change=avg_change,
        previous_critical_assets=prev_crit,
        current_critical_assets=cur_crit,
        critical_assets_change=crit_change,
        previous_high_risk_assets=prev_high,
        current_high_risk_assets=cur_high,
        high_risk_assets_change=high_change,
    )


def detect_latest_risk_change(storage: AssessmentStorage) -> RiskChangeResponse:
    """Fetch the latest two persisted snapshots from storage and compute change metrics.

    Args:
        storage: AssessmentStorage instance

    Returns:
        RiskChangeResponse: Run-over-run risk comparison
    """
    recent_snapshots = storage.list_snapshots(limit=2, order="desc")
    current = recent_snapshots[0] if len(recent_snapshots) > 0 else None
    previous = recent_snapshots[1] if len(recent_snapshots) > 1 else None
    return compute_risk_change(current=current, previous=previous)
