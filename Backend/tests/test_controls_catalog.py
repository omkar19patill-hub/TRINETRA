"""Tests for Security Controls Catalog and Assessment Endpoint

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
from controls import CONTROLS_MODEL_VERSION, get_all_controls, get_control_by_id


REQUIRED_CONTROL_IDS = [
    "CTRL-MFA",
    "CTRL-EDR",
    "CTRL-PATCH",
    "CTRL-BACKUP",
    "CTRL-WAF",
    "CTRL-PAM",
    "CTRL-SIEM",
    "CTRL-TRAIN",
    "CTRL-ZTNA",
    "CTRL-ENCRYPT",
]


def test_control_catalog_completeness():
    """Verify all 10 required standard enterprise controls exist in the catalog."""
    catalog = get_all_controls()
    assert len(catalog) == 10
    catalog_ids = [c.control_id for c in catalog]
    for req_id in REQUIRED_CONTROL_IDS:
        assert req_id in catalog_ids


def test_control_catalog_fields():
    """Verify each control contains all required specification fields."""
    catalog = get_all_controls()
    for ctrl in catalog:
        assert ctrl.control_id and isinstance(ctrl.control_id, str)
        assert ctrl.control_name and isinstance(ctrl.control_name, str)
        assert ctrl.description and isinstance(ctrl.description, str)
        assert ctrl.category and isinstance(ctrl.category, str)
        assert ctrl.implementation_cost >= 0.0
        assert ctrl.annual_cost >= 0.0
        assert ctrl.risk_reduction_effect is not None
        assert isinstance(ctrl.applicable_asset_types, list) and len(ctrl.applicable_asset_types) > 0
        assert isinstance(ctrl.required_dependencies, list)
        assert ctrl.implementation_time >= 0
        assert 0.0 <= ctrl.confidence <= 1.0


def test_control_catalog_specific_dependencies():
    """Verify prerequisite dependencies for PAM, ZTNA, and SIEM."""
    pam = get_control_by_id("CTRL-PAM")
    assert pam is not None
    assert "CTRL-MFA" in pam.required_dependencies

    ztna = get_control_by_id("CTRL-ZTNA")
    assert ztna is not None
    assert "CTRL-MFA" in ztna.required_dependencies

    siem = get_control_by_id("CTRL-SIEM")
    assert siem is not None
    assert "CTRL-EDR" in siem.required_dependencies


def test_api_get_controls():
    """Verify GET /controls returns full catalog with metadata."""
    with TestClient(app) as client:
        res = client.get("/controls")
        assert res.status_code == 200
        data = res.json()
        assert data["total_controls"] == 10
        assert data["version"] == CONTROLS_MODEL_VERSION
        assert len(data["categories"]) >= 5
        assert len(data["controls"]) == 10


def test_api_get_controls_filtered():
    """Verify GET /controls with category and asset_type filters."""
    with TestClient(app) as client:
        # Category filter
        res_cat = client.get("/controls?category=Identity%20%26%20Access")
        assert res_cat.status_code == 200
        data_cat = res_cat.json()
        for c in data_cat["controls"]:
            assert c["category"] == "Identity & Access"

        # Asset type filter
        res_asset = client.get("/controls?asset_type=web_application")
        assert res_asset.status_code == 200
        data_asset = res_asset.json()
        assert data_asset["total_controls"] >= 3


def test_api_post_controls_assess():
    """Verify POST /controls/assess evaluates applicability, dependencies, and quantitative metrics."""
    with TestClient(app) as client:
        payload = {
            "asset_id": "AST-BANK-001",
            "asset_type": "web_application",
            "cvss": 9.8,
            "epss": 0.85,
            "kev": True,
            "internet_exposed": True,
            "criticality": "Critical",
            "existing_controls": ["CTRL-MFA"],
        }
        res = client.post("/controls/assess", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["asset_id"] == "AST-BANK-001"
        assert data["baseline_risk_score"] > 0
        assert data["baseline_eal"] > 0
        assert data["assessed_count"] == 10

        # Find PAM assessment where MFA was already existing
        pam_item = next(item for item in data["assessments"] if item["control_id"] == "CTRL-PAM")
        assert pam_item["dependencies_satisfied"] is True
        assert pam_item["estimated_risk_reduction"] >= 0
        assert pam_item["estimated_eal_avoided"] >= 0


def test_api_post_controls_assess_missing_dependencies():
    """Verify POST /controls/assess flags missing dependencies when prerequisite is not present."""
    with TestClient(app) as client:
        payload = {
            "asset_id": "AST-002",
            "asset_type": "cloud_server",
            "existing_controls": [],  # MFA not present
        }
        res = client.post("/controls/assess", json=payload)
        assert res.status_code == 200
        data = res.json()

        pam_item = next(item for item in data["assessments"] if item["control_id"] == "CTRL-PAM")
        assert pam_item["dependencies_satisfied"] is False
        assert "CTRL-MFA" in pam_item["missing_dependencies"]
        assert "Prerequisite dependency missing" in pam_item["recommendation"]
