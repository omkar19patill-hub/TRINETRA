"""Comprehensive Tests for Deterministic Cybersecurity Investment Optimizer

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from optimization import OPTIMIZATION_MODEL_VERSION, run_optimization
from optimization.schemas import OptimizationRunRequest


def test_unified_optimization_response_contract():
    """Verify POST /optimization/run returns all required specification fields."""
    with TestClient(app) as client:
        payload = {
            "budget_limit": 1800000.0,
            "asset_id": "AST-001",
            "asset_type": "web_application",
            "cvss": 9.8,
            "epss": 0.82,
            "kev": True,
            "internet_exposed": True,
            "criticality": "Critical",
        }
        res = client.post("/optimization/run", json=payload)
        assert res.status_code == 200
        data = res.json()

        # Exact required fields
        required_fields = [
            "selected_controls",
            "rejected_controls",
            "total_cost",
            "remaining_budget",
            "baseline_risk",
            "residual_risk",
            "risk_reduction",
            "baseline_eal",
            "residual_eal",
            "financial_loss_avoided",
            "selection_reasons",
            "rejection_reasons",
            "model_version",
        ]
        for field in required_fields:
            assert field in data, f"Missing required response field: {field}"

        assert data["model_version"] == OPTIMIZATION_MODEL_VERSION
        assert data["total_cost"] <= 1800000.0
        assert round(data["total_cost"] + data["remaining_budget"], 2) == 1800000.0
        assert data["residual_risk"] <= data["baseline_risk"]
        assert data["residual_eal"] <= data["baseline_eal"]
        assert round(data["baseline_risk"] - data["residual_risk"], 2) == round(data["risk_reduction"], 2)
        assert round(data["baseline_eal"] - data["residual_eal"], 2) == round(data["financial_loss_avoided"], 2)
        assert len(data["selected_controls"]) > 0


def test_zero_budget_constraint():
    """Verify zero budget selects 0 controls and provides explicit rejection reasons."""
    with TestClient(app) as client:
        payload = {
            "budget_limit": 0.0,
            "asset_id": "AST-001",
        }
        res = client.post("/optimization/run", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert len(data["selected_controls"]) == 0
        assert data["total_cost"] == 0.0
        assert data["remaining_budget"] == 0.0
        assert data["risk_reduction"] == 0.0
        assert data["financial_loss_avoided"] == 0.0
        assert len(data["rejected_controls"]) == 10

        # Verify rejection reasons mention zero budget
        for cid, reasons in data["rejection_reasons"].items():
            assert any("budget" in r.lower() or "zero" in r.lower() for r in reasons)


def test_insufficient_budget_constraint():
    """Verify budget lower than cheapest control rejects all candidates with budget reasons."""
    with TestClient(app) as client:
        payload = {
            "budget_limit": 50000.0,  # Below cheapest control (₹150,000 for training)
            "asset_id": "AST-001",
        }
        res = client.post("/optimization/run", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert len(data["selected_controls"]) == 0
        assert data["total_cost"] == 0.0
        assert data["remaining_budget"] == 50000.0
        assert len(data["rejected_controls"]) == 10


def test_asset_applicability_filtering():
    """Verify control is rejected when not applicable to the asset archetype."""
    with TestClient(app) as client:
        # Evaluate for asset_type='workstation' where WAF is not applicable (WAF is web_application, api_gateway)
        payload = {
            "budget_limit": 3000000.0,
            "asset_id": "AST-WORKSTATION-01",
            "asset_type": "workstation",
            "candidate_control_ids": ["CTRL-WAF", "CTRL-EDR", "CTRL-MFA"],
        }
        res = client.post("/optimization/run", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert "CTRL-WAF" in data["rejected_controls"]
        waf_reasons = data["rejection_reasons"].get("CTRL-WAF", [])
        assert any("inapplicable" in r.lower() or "not designated" in r.lower() for r in waf_reasons)


def test_dependency_chain_handling():
    """Verify dependent control is selected when dependency is satisfied or bundle fits budget."""
    with TestClient(app) as client:
        # Case A: Candidate is PAM only, but MFA dependency is NOT existing and NOT in candidates
        payload_missing = {
            "budget_limit": 2000000.0,
            "asset_type": "database",
            "candidate_control_ids": ["CTRL-PAM"],
            "existing_controls": [],
        }
        res_a = client.post("/optimization/run", json=payload_missing)
        assert res_a.status_code == 200
        data_a = res_a.json()
        assert "CTRL-PAM" in data_a["rejected_controls"]
        pam_reasons = data_a["rejection_reasons"].get("CTRL-PAM", [])
        assert any("dependency" in r.lower() or "prerequisite" in r.lower() for r in pam_reasons)

        # Case B: MFA is in existing_controls -> PAM can be selected directly
        payload_satisfied = {
            "budget_limit": 2000000.0,
            "asset_type": "database",
            "candidate_control_ids": ["CTRL-PAM"],
            "existing_controls": ["CTRL-MFA"],
        }
        res_b = client.post("/optimization/run", json=payload_satisfied)
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert "CTRL-PAM" in data_b["selected_controls"]


def test_duplicate_controls_handling():
    """Verify passing duplicate controls in candidates pool is handled gracefully."""
    with TestClient(app) as client:
        payload = {
            "budget_limit": 2000000.0,
            "candidate_control_ids": [
                "CTRL-MFA",
                "CTRL-MFA",
                "ctrl-mfa",
                "CTRL-EDR",
                "CTRL-EDR",
            ],
        }
        res = client.post("/optimization/run", json=payload)
        assert res.status_code == 200
        data = res.json()

        # Ensure duplicates are deduplicated
        assert data["selected_controls"].count("CTRL-MFA") <= 1
        assert data["selected_controls"].count("CTRL-EDR") <= 1


def test_deterministic_reproducibility():
    """Verify optimizer execution is 100% deterministic (identical inputs produce identical outputs)."""
    with TestClient(app) as client:
        payload = {
            "budget_limit": 1500000.0,
            "asset_id": "AST-001",
            "cvss": 9.5,
            "epss": 0.75,
            "kev": True,
            "internet_exposed": True,
            "criticality": "High",
        }
        res1 = client.post("/optimization/run", json=payload)
        res2 = client.post("/optimization/run", json=payload)

        assert res1.status_code == 200
        assert res2.status_code == 200

        data1 = res1.json()
        data2 = res2.json()

        assert data1["selected_controls"] == data2["selected_controls"]
        assert data1["total_cost"] == data2["total_cost"]
        assert data1["residual_risk"] == data2["residual_risk"]
        assert data1["residual_eal"] == data2["residual_eal"]
        assert data1["financial_loss_avoided"] == data2["financial_loss_avoided"]


def test_before_after_analysis_endpoint():
    """Verify POST /optimization/before-after calculates comprehensive baseline vs residual metrics."""
    with TestClient(app) as client:
        payload = {
            "run_parameters": {
                "budget_limit": 1800000.0,
                "asset_id": "AST-001",
                "asset_type": "web_application",
                "cvss": 9.8,
                "epss": 0.82,
                "kev": True,
                "internet_exposed": True,
                "criticality": "Critical",
            }
        }
        res = client.post("/optimization/before-after", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert "baseline" in data
        assert "residual" in data
        assert "deltas" in data
        assert len(data["controls_applied"]) > 0

        baseline = data["baseline"]
        residual = data["residual"]
        deltas = data["deltas"]

        assert baseline["risk_score"] > residual["risk_score"]
        assert baseline["expected_annual_loss"] > residual["expected_annual_loss"]
        assert deltas["risk_reduction_points"] > 0
        assert deltas["financial_loss_avoided"] > 0
        assert deltas["total_investment_cost"] > 0
        assert deltas["return_on_security_investment"] is not None


def test_invalid_input_error_handling():
    """Verify negative budget limit returns HTTP 422 unprocessable entity."""
    with TestClient(app) as client:
        payload = {
            "budget_limit": -100000.0,
        }
        res = client.post("/optimization/run", json=payload)
        assert res.status_code == 422


def test_selected_and_rejected_controls_are_control_id_strings():
    """Both control lists must contain stable control ID strings, not objects.

    Guards the List[str] contract on OptimizationRunResponse. response_model
    validation is active on POST /optimization/run, so a non-string value would
    now fail at the response boundary rather than being passed through silently.
    Covers the default catalog path and the custom_controls path, the latter
    being the only route by which caller-supplied data reaches these fields.
    """
    from controls.catalog import get_all_controls

    custom = get_all_controls()[0].model_dump()
    custom["control_id"] = "CTRL-CUSTOM"
    custom["control_name"] = "Custom Regression Control"

    cases = {
        "default": {"budget_limit": 1800000.0, "asset_id": "AST-001"},
        "custom_controls": {
            "budget_limit": 2000000.0,
            "asset_id": "AST-001",
            "custom_controls": [custom],
        },
    }

    with TestClient(app) as client:
        for case_name, payload in cases.items():
            res = client.post("/optimization/run", json=payload)
            assert res.status_code == 200, f"{case_name} returned {res.status_code}"
            data = res.json()

            for field in ("selected_controls", "rejected_controls"):
                values = data[field]
                assert isinstance(values, list)
                for value in values:
                    assert isinstance(value, str), (
                        f"{case_name}: {field} contained a non-string {value!r}"
                    )
                    assert value.startswith("CTRL-"), (
                        f"{case_name}: {field} contained {value!r}, expected a CTRL- ID"
                    )

        # The custom control must actually have been considered, so the
        # custom_controls path is genuinely exercised rather than passing vacuously.
        res = client.post("/optimization/run", json=cases["custom_controls"])
        data = res.json()
        assert "CTRL-CUSTOM" in data["selected_controls"] + data["rejected_controls"]
