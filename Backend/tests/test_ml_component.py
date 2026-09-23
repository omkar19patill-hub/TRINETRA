"""Comprehensive Automated Tests for Explainable ML Risk Calibration Component

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Explainable ML Risk Calibration Component

Tests:
1. Model loading & health endpoint (/ml/health, /ml/model-info)
2. Valid high-risk & low-risk predictions (/ml/predict)
3. Input validation & error handling (invalid CVSS, EPSS, criticality)
4. Probability bounds [0.0, 1.0] across wide parameter sweeps
5. Feature-level log-odds explainability integrity
6. Missing model file fallback self-training
7. Auxiliary signal integrity & governance compliance
"""

import hashlib
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from ml import ML_MODEL_VERSION
from ml.model import RiskCalibrationModel, get_model
from ml.schemas import MLPredictionRequest


@pytest.fixture
def test_client():
    """Create a FastAPI TestClient."""
    return TestClient(app)


def test_ml_health_endpoint(test_client):
    """Verify GET /ml/health returns operational status and model loaded flag."""
    response = test_client.get("/ml/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["module"] == "ml-risk-calibration"
    assert data["model_version"] == ML_MODEL_VERSION
    assert data["model_loaded"] is True


def test_ml_model_info_endpoint(test_client):
    """Verify GET /ml/model-info returns complete architecture disclosures and accuracy."""
    response = test_client.get("/ml/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "Logistic Regression" in data["algorithm"]
    assert data["model_version"] == ML_MODEL_VERSION
    assert "cvss" in data["features"]
    assert "epss" in data["features"]
    assert "criticality" in data["features"]
    assert data["accuracy"] > 0.85
    assert data["roc_auc"] > 0.90
    assert "synthetic" in data["synthetic_data_notice"].lower()
    assert "auxiliary" in data["auxiliary_role_statement"].lower()


def test_valid_high_risk_prediction(test_client):
    """Verify that severe vulnerability on critical exposed asset predicts high-impact event (class 1)."""
    payload = {
        "asset_id": "AST-CRIT-001",
        "cve_id": "CVE-2026-9999",
        "cvss": 9.8,
        "epss": 0.89,
        "kev": True,
        "internet_exposed": True,
        "criticality": "Critical",
        "asset_type": "Database",
        "business_service": "Payment Gateway",
    }
    response = test_client.post("/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["asset_id"] == "AST-CRIT-001"
    assert data["cve_id"] == "CVE-2026-9999"
    assert data["predicted_class"] == 1
    assert data["classification_label"] == "High-Impact Event"
    assert data["ml_risk_probability"] >= 0.70
    assert data["model_version"] == ML_MODEL_VERSION
    assert len(data["feature_contributions"]) >= 5

    # Check top feature contribution increases risk
    top_contrib = data["feature_contributions"][0]
    assert top_contrib["direction"] == "increases_risk"
    assert top_contrib["weight"] > 0


def test_valid_low_risk_prediction(test_client):
    """Verify that mild vulnerability on internal low-criticality asset predicts standard severity (class 0)."""
    payload = {
        "asset_id": "AST-INT-002",
        "cve_id": "CVE-2026-1111",
        "cvss": 2.5,
        "epss": 0.01,
        "kev": False,
        "internet_exposed": False,
        "criticality": "Low",
        "asset_type": "Workstation",
        "business_service": "Internal Operations",
    }
    response = test_client.post("/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["predicted_class"] == 0
    assert data["classification_label"] == "Standard Severity Event"
    assert data["ml_risk_probability"] <= 0.35


def test_probability_range_strictly_bounded(test_client):
    """Verify that output probability is strictly bounded within [0.0, 1.0] across edge cases."""
    edge_cases = [
        {"cvss": 0.0, "epss": 0.0, "kev": False, "internet_exposed": False, "criticality": "Low"},
        {"cvss": 10.0, "epss": 1.0, "kev": True, "internet_exposed": True, "criticality": "Critical"},
        {"cvss": 5.0, "epss": 0.5, "kev": False, "internet_exposed": True, "criticality": "Medium"},
    ]
    for case in edge_cases:
        response = test_client.post("/ml/predict", json=case)
        assert response.status_code == 200
        prob = response.json()["ml_risk_probability"]
        assert 0.0 <= prob <= 1.0


def test_invalid_inputs_rejected(test_client):
    """Verify input validation rejects illegal parameter values with HTTP 422."""
    # 1. Negative CVSS
    r1 = test_client.post("/ml/predict", json={"cvss": -1.0, "epss": 0.5, "kev": False, "internet_exposed": False, "criticality": "High"})
    assert r1.status_code == 422

    # 2. CVSS > 10
    r2 = test_client.post("/ml/predict", json={"cvss": 10.5, "epss": 0.5, "kev": False, "internet_exposed": False, "criticality": "High"})
    assert r2.status_code == 422

    # 3. EPSS > 1.0
    r3 = test_client.post("/ml/predict", json={"cvss": 8.0, "epss": 1.5, "kev": False, "internet_exposed": False, "criticality": "High"})
    assert r3.status_code == 422

    # 4. Invalid criticality
    r4 = test_client.post("/ml/predict", json={"cvss": 8.0, "epss": 0.5, "kev": False, "internet_exposed": False, "criticality": "Catastrophic"})
    assert r4.status_code == 422


def test_feature_contributions_explainability_structure(test_client):
    """Verify feature contributions contain clear descriptions and valid mathematical directions."""
    payload = {
        "cvss": 8.5,
        "epss": 0.70,
        "kev": True,
        "internet_exposed": True,
        "criticality": "High",
    }
    response = test_client.post("/ml/predict", json=payload)
    assert response.status_code == 200
    contributions = response.json()["feature_contributions"]

    assert len(contributions) == 7
    for c in contributions:
        assert "feature" in c and isinstance(c["feature"], str)
        assert "value" in c
        assert "weight" in c and isinstance(c["weight"], (int, float))
        assert c["direction"] in {"increases_risk", "decreases_risk", "neutral"}
        assert len(c["description"]) > 0


def test_missing_model_file_fallback(tmp_path):
    """Verify that RiskCalibrationModel handles a non-existent artifact path gracefully via auto-training."""
    dummy_path = tmp_path / "non_existent_model.joblib"
    assert not dummy_path.exists()

    model = RiskCalibrationModel(model_path=dummy_path)
    assert model.is_loaded

    req = MLPredictionRequest(
        cvss=8.0,
        epss=0.40,
        kev=True,
        internet_exposed=True,
        criticality="High",
    )
    result = model.predict(req)
    assert 0.0 <= result.ml_risk_probability <= 1.0
    assert result.predicted_class in {0, 1}


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file's contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fallback_training_does_not_touch_repository_artifacts(tmp_path):
    """Fallback self-training must write only to the injected paths.

    Regression test: train_and_save_model() previously wrote to hardcoded module
    paths, so constructing a model against a temporary directory silently
    overwrote the tracked ml/model.joblib and data/ml_training.csv.
    """
    from ml.train import DATASET_PATH, MODEL_PATH

    tracked_model_before = _sha256(MODEL_PATH)
    tracked_dataset_before = _sha256(DATASET_PATH)

    temp_model = tmp_path / "model.joblib"
    temp_dataset = tmp_path / "ml_training.csv"
    assert not temp_model.exists()
    assert not temp_dataset.exists()

    model = RiskCalibrationModel(model_path=temp_model)
    assert model.is_loaded

    # Training wrote both artifacts inside the temporary directory
    assert temp_model.exists(), "artifact was not written to the injected model path"
    assert temp_dataset.exists(), "dataset was not written beside the injected model path"

    # The tracked repository copies are untouched
    assert _sha256(MODEL_PATH) == tracked_model_before, "tracked model.joblib was modified"
    assert _sha256(DATASET_PATH) == tracked_dataset_before, "tracked ml_training.csv was modified"


def test_fallback_training_accepts_explicit_dataset_path(tmp_path):
    """An explicitly supplied dataset path is honoured over the derived default."""
    from ml.train import DATASET_PATH, MODEL_PATH

    tracked_model_before = _sha256(MODEL_PATH)
    tracked_dataset_before = _sha256(DATASET_PATH)

    temp_model = tmp_path / "artifact" / "model.joblib"
    temp_dataset = tmp_path / "dataset" / "training.csv"

    model = RiskCalibrationModel(model_path=temp_model, dataset_path=temp_dataset)
    assert model.is_loaded

    assert temp_model.exists()
    assert temp_dataset.exists(), "explicit dataset_path was not used"

    assert _sha256(MODEL_PATH) == tracked_model_before
    assert _sha256(DATASET_PATH) == tracked_dataset_before


def test_default_paths_still_resolve_to_repository_artifacts():
    """Default construction must keep using the repository artifact (no behaviour change)."""
    from ml.model import MODEL_PATH as MODEL_MODULE_PATH
    from ml.train import DATASET_PATH, MODEL_PATH

    model = RiskCalibrationModel()
    assert model.model_path == MODEL_MODULE_PATH
    assert model.model_path == MODEL_PATH
    # No explicit dataset path means train.py applies its own default
    assert model.dataset_path is None
    assert model._resolve_dataset_path() is None
    assert DATASET_PATH.exists()


def test_unified_root_endpoint_includes_ml():
    """Verify root GET / metadata reports ML Risk Calibration module and endpoints."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()

        assert "ML Risk Calibration" in data["modules"]
        assert data["ml_model_version"] == ML_MODEL_VERSION
        endpoints = data["endpoints"]
        assert endpoints["ml_predict"] == "/ml/predict"
        assert endpoints["ml_model_info"] == "/ml/model-info"
        assert endpoints["ml_health"] == "/ml/health"
