"""Comprehensive Automated Tests for Control Dependency Resolution

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Tests:
5. Single dependency is resolved.
6. Multiple dependencies are resolved.
7. Nested dependencies are resolved.
8. Duplicate dependencies are not double-counted.
9. Inapplicable dependency is rejected.
10. Missing dependency is rejected.
11. Circular dependency is detected.
12. Dependency bundle exceeds budget.
13. Zero budget handling.
14. Negative budget rejection.
15. Duplicate requested controls deduplication.
+ API endpoint validation (/controls/resolve-dependencies).
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from controls.catalog import get_all_controls, get_control_by_id
from controls.models import RiskReductionEffect, SecurityControl
from controls.resolver import (
    CircularDependencyError,
    ControlDependencyResolver,
    is_control_applicable,
)


def test_5_single_dependency_resolved():
    """Verify single prerequisite dependency (CTRL-PAM requires CTRL-MFA) is correctly resolved and bundled."""
    resolver = ControlDependencyResolver(
        asset_type="cloud_server",
        budget_limit=1500000.0,
        existing_controls=[],
    )
    pam = get_control_by_id("CTRL-PAM")
    assert pam is not None
    assert "CTRL-MFA" in pam.required_dependencies

    res = resolver.resolve_bundle(
        control=pam,
        already_selected_ids=set(),
        remaining_budget=1500000.0,
    )
    assert res.status == "selected"
    assert res.rejection_reason is None
    # Bundle cost = PAM (700,000) + MFA (350,000) = 1,050,000
    assert res.bundle_cost == 1050000.0
    assert len(res.dependencies) == 1
    dep = res.dependencies[0]
    assert dep.control_id == "CTRL-MFA"
    assert dep.status == "included"
    assert dep.reason == "Required dependency"


def test_6_multiple_dependencies_resolved():
    """Verify multiple prerequisite dependencies on a single control are all resolved."""
    custom_ctrl = SecurityControl(
        control_id="CTRL-MULTI",
        control_name="Multi-Dependency Control",
        description="Requires both MFA and EDR",
        category="Technical",
        implementation_cost=200000.0,
        annual_cost=30000.0,
        applicable_asset_types=["cloud_server", "all"],
        required_dependencies=["CTRL-MFA", "CTRL-EDR"],
        implementation_time=14,
    )

    resolver = ControlDependencyResolver(
        controls_pool=[custom_ctrl],
        asset_type="cloud_server",
        budget_limit=2000000.0,
    )

    res = resolver.resolve_bundle(
        control=custom_ctrl,
        already_selected_ids=set(),
        remaining_budget=2000000.0,
    )
    assert res.status == "selected"
    # Cost = 200,000 (ctrl) + 350,000 (MFA) + 600,000 (EDR) = 1,150,000
    assert res.bundle_cost == 1150000.0
    assert len(res.dependencies) == 2
    dep_ids = [d.control_id for d in res.dependencies]
    assert "CTRL-MFA" in dep_ids
    assert "CTRL-EDR" in dep_ids
    assert all(d.status == "included" for d in res.dependencies)


def test_7_nested_dependencies_resolved():
    """Verify nested transitive dependencies (A -> B -> C) are resolved recursively in correct order."""
    ctrl_c = SecurityControl(
        control_id="CTRL-C",
        control_name="Control C Base",
        description="Foundation control",
        category="Technical",
        implementation_cost=100000.0,
        annual_cost=10000.0,
        applicable_asset_types=["all"],
        required_dependencies=[],
        implementation_time=7,
    )
    ctrl_b = SecurityControl(
        control_id="CTRL-B",
        control_name="Control B Intermediate",
        description="Depends on C",
        category="Technical",
        implementation_cost=200000.0,
        annual_cost=20000.0,
        applicable_asset_types=["all"],
        required_dependencies=["CTRL-C"],
        implementation_time=14,
    )
    ctrl_a = SecurityControl(
        control_id="CTRL-A",
        control_name="Control A Top",
        description="Depends on B",
        category="Technical",
        implementation_cost=300000.0,
        annual_cost=30000.0,
        applicable_asset_types=["all"],
        required_dependencies=["CTRL-B"],
        implementation_time=21,
    )

    resolver = ControlDependencyResolver(
        controls_pool=[ctrl_a, ctrl_b, ctrl_c],
        asset_type="web_application",
        budget_limit=1000000.0,
    )

    res = resolver.resolve_bundle(
        control=ctrl_a,
        already_selected_ids=set(),
        remaining_budget=1000000.0,
    )
    assert res.status == "selected"
    # Bundle cost = Cost(A) + Cost(B) + Cost(C) = 300k + 200k + 100k = 600,000
    assert res.bundle_cost == 600000.0
    dep_ids = [d.control_id for d in res.dependencies]
    assert "CTRL-C" in dep_ids
    assert "CTRL-B" in dep_ids


def test_8_duplicate_dependencies_not_double_counted():
    """Verify shared dependencies (diamond pattern A -> B, C; B -> C) count dependency costs exactly once."""
    ctrl_c = SecurityControl(
        control_id="CTRL-SHARED-C",
        control_name="Shared Base",
        description="Shared dependency",
        category="Technical",
        implementation_cost=100000.0,
        annual_cost=10000.0,
        applicable_asset_types=["all"],
        required_dependencies=[],
        implementation_time=7,
    )
    ctrl_b = SecurityControl(
        control_id="CTRL-SHARED-B",
        control_name="Intermediate B",
        description="Depends on Shared Base",
        category="Technical",
        implementation_cost=200000.0,
        annual_cost=20000.0,
        applicable_asset_types=["all"],
        required_dependencies=["CTRL-SHARED-C"],
        implementation_time=14,
    )
    ctrl_a = SecurityControl(
        control_id="CTRL-SHARED-A",
        control_name="Top A",
        description="Depends on both B and Shared Base",
        category="Technical",
        implementation_cost=300000.0,
        annual_cost=30000.0,
        applicable_asset_types=["all"],
        required_dependencies=["CTRL-SHARED-B", "CTRL-SHARED-C"],
        implementation_time=21,
    )

    resolver = ControlDependencyResolver(
        controls_pool=[ctrl_a, ctrl_b, ctrl_c],
        asset_type="web_application",
        budget_limit=1000000.0,
    )

    res = resolver.resolve_bundle(
        control=ctrl_a,
        already_selected_ids=set(),
        remaining_budget=1000000.0,
    )
    assert res.status == "selected"
    # Cost should be counted ONCE for C: 300k + 200k + 100k = 600,000 (NOT 700,000)
    assert res.bundle_cost == 600000.0

    # Test when dependency is already in existing_controls: cost is 0
    resolver_with_existing = ControlDependencyResolver(
        controls_pool=[ctrl_a, ctrl_b, ctrl_c],
        asset_type="web_application",
        budget_limit=1000000.0,
        existing_controls=["CTRL-SHARED-C"],
    )
    res_existing = resolver_with_existing.resolve_bundle(
        control=ctrl_a,
        already_selected_ids=set(),
        remaining_budget=1000000.0,
    )
    # Cost should not include CTRL-SHARED-C: 300k + 200k = 500,000
    assert res_existing.bundle_cost == 500000.0


def test_9_inapplicable_dependency_rejected():
    """Verify that a control whose prerequisite dependency is inapplicable to the asset is rejected."""
    # Data Encryption is applicable ONLY to database and cloud_server
    enc = get_control_by_id("CTRL-ENCRYPT")
    assert enc is not None
    assert "web_application" not in enc.applicable_asset_types

    # Create control applicable to web_application that requires Data Encryption
    web_ctrl = SecurityControl(
        control_id="CTRL-WEB-APP",
        control_name="Web App Custom Control",
        description="Requires database encryption",
        category="Application Security",
        implementation_cost=250000.0,
        annual_cost=30000.0,
        applicable_asset_types=["web_application"],
        required_dependencies=["CTRL-ENCRYPT"],
        implementation_time=14,
    )

    resolver = ControlDependencyResolver(
        controls_pool=[web_ctrl],
        asset_type="web_application",
        budget_limit=1000000.0,
    )

    res = resolver.resolve_bundle(
        control=web_ctrl,
        already_selected_ids=set(),
        remaining_budget=1000000.0,
    )
    assert res.status == "rejected"
    assert res.rejection_reason == "Required dependency cannot be satisfied"
    assert len(res.dependencies) == 1
    assert res.dependencies[0].control_id == "CTRL-ENCRYPT"
    assert res.dependencies[0].status == "unavailable"
    assert "not applicable" in res.dependencies[0].reason.lower()


def test_10_missing_dependency_rejected():
    """Verify that a control requiring a non-existent control ID is safely rejected."""
    bad_ctrl = SecurityControl(
        control_id="CTRL-ORPHAN",
        control_name="Orphaned Control",
        description="Requires missing dependency",
        category="Technical",
        implementation_cost=100000.0,
        annual_cost=10000.0,
        applicable_asset_types=["all"],
        required_dependencies=["CTRL-DOES-NOT-EXIST"],
        implementation_time=7,
    )

    resolver = ControlDependencyResolver(
        controls_pool=[bad_ctrl],
        asset_type="web_application",
        budget_limit=1000000.0,
    )

    res = resolver.resolve_bundle(
        control=bad_ctrl,
        already_selected_ids=set(),
        remaining_budget=1000000.0,
    )
    assert res.status == "rejected"
    assert res.rejection_reason == "Required dependency cannot be satisfied"
    assert any(d.control_id == "CTRL-DOES-NOT-EXIST" for d in res.dependencies)
    assert any(d.status == "unavailable" for d in res.dependencies)


def test_11_circular_dependency_detected():
    """Verify that circular dependency chains (A -> B -> A) raise 'Circular control dependency detected.'"""
    ctrl_a = SecurityControl(
        control_id="CTRL-CIRC-A",
        control_name="Circular A",
        description="Requires B",
        category="Technical",
        implementation_cost=100000.0,
        annual_cost=10000.0,
        applicable_asset_types=["all"],
        required_dependencies=["CTRL-CIRC-B"],
        implementation_time=7,
    )
    ctrl_b = SecurityControl(
        control_id="CTRL-CIRC-B",
        control_name="Circular B",
        description="Requires A",
        category="Technical",
        implementation_cost=100000.0,
        annual_cost=10000.0,
        applicable_asset_types=["all"],
        required_dependencies=["CTRL-CIRC-A"],
        implementation_time=7,
    )

    resolver = ControlDependencyResolver(
        controls_pool=[ctrl_a, ctrl_b],
        asset_type="web_application",
        budget_limit=1000000.0,
    )

    with pytest.raises(ValueError) as exc_info:
        resolver.detect_cycles(["CTRL-CIRC-A"])
    assert "Circular control dependency detected" in str(exc_info.value)

    # Also test resolve_all detects the cycle
    with pytest.raises(CircularDependencyError) as exc_info2:
        resolver.resolve_all([ctrl_a, ctrl_b])
    assert "Circular control dependency detected" in str(exc_info2.value)


def test_12_dependency_bundle_exceeds_budget():
    """Verify that when a dependency bundle cost exceeds available budget, control is rejected with clear reasons."""
    pam = get_control_by_id("CTRL-PAM")
    assert pam is not None
    # PAM (700,000) + MFA (350,000) = 1,050,000
    # Available budget: 800,000 (enough for PAM alone, but NOT bundle with MFA)
    resolver = ControlDependencyResolver(
        asset_type="cloud_server",
        budget_limit=800000.0,
        existing_controls=[],
    )

    res = resolver.resolve_bundle(
        control=pam,
        already_selected_ids=set(),
        remaining_budget=800000.0,
    )
    assert res.status == "rejected"
    assert res.rejection_reason == "Required dependency cannot be satisfied"
    assert len(res.dependencies) == 1
    dep = res.dependencies[0]
    assert dep.control_id == "CTRL-MFA"
    assert dep.status == "unavailable"
    assert "exceeds budget" in dep.reason.lower() or "not applicable" in dep.reason.lower()


def test_13_zero_budget():
    """Verify zero budget correctly rejects controls with implementation cost > 0."""
    resolver = ControlDependencyResolver(
        asset_type="web_application",
        budget_limit=0.0,
        existing_controls=[],
    )
    mfa = get_control_by_id("CTRL-MFA")
    assert mfa is not None

    res = resolver.resolve_bundle(
        control=mfa,
        already_selected_ids=set(),
        remaining_budget=0.0,
    )
    assert res.status == "rejected"
    assert "budget" in res.rejection_reason.lower()


def test_14_negative_budget():
    """Verify negative budget is rejected immediately with ValueError."""
    with pytest.raises(ValueError) as exc_info:
        ControlDependencyResolver(
            asset_type="web_application",
            budget_limit=-50000.0,
        )
    assert "non-negative" in str(exc_info.value).lower()


def test_15_duplicate_requested_controls():
    """Verify duplicate requested controls are deduplicated and costs are counted exactly once."""
    mfa = get_control_by_id("CTRL-MFA")
    edr = get_control_by_id("CTRL-EDR")
    assert mfa is not None and edr is not None

    resolver = ControlDependencyResolver(
        asset_type="workstation",
        budget_limit=2000000.0,
    )

    # Pass MFA twice
    resolutions = resolver.resolve_all([mfa, mfa, edr])
    # Deduplicated list of resolutions
    assert len(resolutions) == 2
    res_mfa = resolutions[0]
    res_edr = resolutions[1]
    assert res_mfa.control_id == "CTRL-MFA"
    assert res_mfa.status == "selected"
    assert res_edr.control_id == "CTRL-EDR"
    assert res_edr.status == "selected"
    # Total combined cost should be 350k + 600k = 950k, not double-counted MFA
    total_cost = res_mfa.bundle_cost + res_edr.bundle_cost
    assert total_cost == 950000.0


def test_api_resolve_dependencies_endpoint():
    """Verify POST /controls/resolve-dependencies endpoint returns structured schema."""
    with TestClient(app) as client:
        payload = {
            "requested_control_ids": ["CTRL-PAM", "CTRL-MFA"],
            "asset_id": "AST-001",
            "asset_type": "cloud_server",
            "budget_limit": 1500000.0,
            "existing_controls": [],
        }
        res = client.post("/controls/resolve-dependencies", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 2

        pam_item = next(item for item in data if item["control_id"] == "CTRL-PAM")
        assert pam_item["status"] == "selected"
        assert pam_item["bundle_cost"] > 0
        assert len(pam_item["dependencies"]) == 1
        assert pam_item["dependencies"][0]["control_id"] == "CTRL-MFA"
        assert pam_item["dependencies"][0]["status"] == "included"


def test_api_resolve_dependencies_negative_budget_rejected():
    """Verify POST /controls/resolve-dependencies rejects negative budget with 422."""
    with TestClient(app) as client:
        payload = {
            "requested_control_ids": ["CTRL-MFA"],
            "budget_limit": -1000.0,
        }
        res = client.post("/controls/resolve-dependencies", json=payload)
        assert res.status_code == 422
