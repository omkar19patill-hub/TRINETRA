"""Local Decision Assessment Store & Tamper Simulation Registry (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Manages local quantitative assessment records (inputs + computed outputs)
and allows seamless verification against immutable blockchain anchors.
"""

import copy
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .hashing import (
    compute_composite_hash,
    compute_data_snapshot_hash,
    compute_result_hash,
)

_LOCK = threading.Lock()
_ASSESSMENT_STORE: Dict[str, Dict[str, Any]] = {}
_ORIGINAL_BACKUP_STORE: Dict[str, Dict[str, Any]] = {}


def _get_benchmark_crq_001() -> Dict[str, Any]:
    """Return canonical assessment payload for benchmark CRQ-001."""
    data_snapshot = {
        "assessment_id": "CRQ-001",
        "asset_id": "AST-001",
        "asset_criticality": "Critical",
        "internet_exposed": True,
        "cve_id": "CVE-2026-1234",
        "cvss_score": 9.8,
        "epss_score": 0.82,
        "kev_status": True,
        "budget_limit": 1800000.0,
        "revenue_loss_per_hour": 150000.0,
        "downtime_hours_estimate": 10.0,
        "incident_response_cost": 250000.0,
        "recovery_cost": 300000.0,
        "regulatory_fine_estimate": 400000.0,
    }

    decision_result = {
        "assessment_id": "CRQ-001",
        "decision_id": "OPT-001",
        "risk_score": 94.2,
        "risk_category": "CRITICAL",
        "modeled_annual_frequency": 0.738,
        "total_loss_magnitude": 2450000.0,
        "expected_annual_loss": 1808100.0,
        "monte_carlo_p50_loss": 1780000.0,
        "monte_carlo_p90_loss": 3150000.0,
        "monte_carlo_p99_loss": 5200000.0,
        "selected_portfolio": {
            "portfolio_id": "portfolio-balanced-roi",
            "name": "Balanced ROI & Cost-Efficiency",
            "total_cost": 1400000.0,
            "risk_reduction": 2530000.0,
            "residual_risk": 2470000.0,
            "selected_controls": ["CTRL-MFA", "CTRL-EDR", "CTRL-BACKUP"],
        },
    }

    snapshot_hash = compute_data_snapshot_hash(data_snapshot)
    result_hash = compute_result_hash(decision_result)
    timestamp = "2026-09-20T12:00:00Z"
    canonical_hash = compute_composite_hash(
        assessment_id="CRQ-001",
        decision_id="OPT-001",
        model_version="1.0",
        timestamp=timestamp,
        data_snapshot_hash=snapshot_hash,
        result_hash=result_hash,
    )

    return {
        "assessment_id": "CRQ-001",
        "decision_id": "OPT-001",
        "model_version": "1.0",
        "timestamp": timestamp,
        "data_snapshot": data_snapshot,
        "decision_result": decision_result,
        "data_snapshot_hash": snapshot_hash,
        "result_hash": result_hash,
        "canonical_hash": canonical_hash,
        "is_tampered": False,
    }


def _get_benchmark_crq_enterprise() -> Dict[str, Any]:
    """Return canonical assessment payload for enterprise banking scenario."""
    data_snapshot = {
        "assessment_id": "CRQ-ENTERPRISE-001",
        "asset_id": "AST-BANK-CORE",
        "asset_criticality": "Critical",
        "internet_exposed": True,
        "cve_id": "CVE-2021-44228",
        "cvss_score": 10.0,
        "epss_score": 0.975,
        "kev_status": True,
        "budget_limit": 2500000.0,
        "revenue_loss_per_hour": 500000.0,
        "downtime_hours_estimate": 12.0,
        "incident_response_cost": 800000.0,
        "recovery_cost": 750000.0,
        "regulatory_fine_estimate": 1500000.0,
    }

    decision_result = {
        "assessment_id": "CRQ-ENTERPRISE-001",
        "decision_id": "OPT-ENTERPRISE-001",
        "risk_score": 98.6,
        "risk_category": "CRITICAL",
        "modeled_annual_frequency": 0.975,
        "total_loss_magnitude": 9050000.0,
        "expected_annual_loss": 8823750.0,
        "monte_carlo_p50_loss": 8600000.0,
        "monte_carlo_p90_loss": 14200000.0,
        "monte_carlo_p99_loss": 21500000.0,
        "selected_portfolio": {
            "portfolio_id": "portfolio-max-risk-reduction",
            "name": "Maximum Risk Reduction Portfolio",
            "total_cost": 2400000.0,
            "risk_reduction": 3600000.0,
            "residual_risk": 4900000.0,
            "selected_controls": ["CTRL-MFA", "CTRL-EDR", "CTRL-PAM", "CTRL-BACKUP"],
        },
    }

    snapshot_hash = compute_data_snapshot_hash(data_snapshot)
    result_hash = compute_result_hash(decision_result)
    timestamp = "2026-09-20T12:30:00Z"
    canonical_hash = compute_composite_hash(
        assessment_id="CRQ-ENTERPRISE-001",
        decision_id="OPT-ENTERPRISE-001",
        model_version="1.0",
        timestamp=timestamp,
        data_snapshot_hash=snapshot_hash,
        result_hash=result_hash,
    )

    return {
        "assessment_id": "CRQ-ENTERPRISE-001",
        "decision_id": "OPT-ENTERPRISE-001",
        "model_version": "1.0",
        "timestamp": timestamp,
        "data_snapshot": data_snapshot,
        "decision_result": decision_result,
        "data_snapshot_hash": snapshot_hash,
        "result_hash": result_hash,
        "canonical_hash": canonical_hash,
        "is_tampered": False,
    }


def seed_benchmark_assessments() -> None:
    """Populate initial local assessments."""
    b1 = _get_benchmark_crq_001()
    b2 = _get_benchmark_crq_enterprise()

    with _LOCK:
        _ASSESSMENT_STORE[b1["assessment_id"]] = copy.deepcopy(b1)
        _ORIGINAL_BACKUP_STORE[b1["assessment_id"]] = copy.deepcopy(b1)

        _ASSESSMENT_STORE[b2["assessment_id"]] = copy.deepcopy(b2)
        _ORIGINAL_BACKUP_STORE[b2["assessment_id"]] = copy.deepcopy(b2)


def get_assessment(assessment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an assessment by ID."""
    if not _ASSESSMENT_STORE:
        seed_benchmark_assessments()
    with _LOCK:
        return _ASSESSMENT_STORE.get(assessment_id) or _ASSESSMENT_STORE.get(assessment_id.strip())


def save_assessment(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store or update an assessment record locally."""
    assessment_id = assessment_data["assessment_id"]
    with _LOCK:
        _ASSESSMENT_STORE[assessment_id] = copy.deepcopy(assessment_data)
        if assessment_id not in _ORIGINAL_BACKUP_STORE:
            _ORIGINAL_BACKUP_STORE[assessment_id] = copy.deepcopy(assessment_data)
        return _ASSESSMENT_STORE[assessment_id]


def list_assessments() -> List[Dict[str, Any]]:
    """List all stored local assessments."""
    if not _ASSESSMENT_STORE:
        seed_benchmark_assessments()
    with _LOCK:
        return list(_ASSESSMENT_STORE.values())


def tamper_assessment(
    assessment_id: str,
    tamper_type: str = "modify_eal",
    custom_value: Optional[Any] = None,
) -> Dict[str, Any]:
    """Simulate unauthorized data tampering on local result to test blockchain verification failure."""
    assessment = get_assessment(assessment_id)
    if not assessment:
        raise KeyError(f"Assessment '{assessment_id}' not found in local store.")

    with _LOCK:
        rec = _ASSESSMENT_STORE[assessment_id]
        rec["is_tampered"] = True

        if tamper_type == "modify_eal":
            new_val = custom_value if custom_value is not None else 999999.0
            if "decision_result" in rec and isinstance(rec["decision_result"], dict):
                rec["decision_result"]["expected_annual_loss"] = float(new_val)
        elif tamper_type == "modify_portfolio":
            if "decision_result" in rec and "selected_portfolio" in rec["decision_result"]:
                rec["decision_result"]["selected_portfolio"]["selected_controls"] = ["CTRL-NONE-UNAUTHORIZED"]
        elif tamper_type == "modify_snapshot":
            if "data_snapshot" in rec and isinstance(rec["data_snapshot"], dict):
                rec["data_snapshot"]["asset_criticality"] = "Low"
        elif tamper_type == "corrupt_hash":
            rec["result_hash"] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

        return copy.deepcopy(rec)


def reset_assessment(assessment_id: str) -> Optional[Dict[str, Any]]:
    """Restore an assessment to its pristine, original untampered state."""
    with _LOCK:
        if assessment_id in _ORIGINAL_BACKUP_STORE:
            _ASSESSMENT_STORE[assessment_id] = copy.deepcopy(_ORIGINAL_BACKUP_STORE[assessment_id])
            return _ASSESSMENT_STORE[assessment_id]
        return None


# Seed on module import
seed_benchmark_assessments()
