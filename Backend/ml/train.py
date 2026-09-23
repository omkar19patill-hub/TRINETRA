"""Synthetic Dataset Generator & Logistic Regression Model Training Pipeline

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Explainable ML Risk Calibration Component

Generates synthetic training records (data/ml_training.csv) and trains
an explainable Logistic Regression classifier saved to ml/model.joblib.
"""

import math
from pathlib import Path
from typing import Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import ML_MODEL_VERSION


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_PATH = BASE_DIR / "ml" / "model.joblib"
DATASET_PATH = DATA_DIR / "ml_training.csv"

CRITICALITIES = ["Critical", "High", "Medium", "Low"]
ASSET_TYPES = [
    "Application Gateway",
    "Database",
    "Web Server",
    "API Service",
    "Workstation",
    "Cloud Storage",
]
BUSINESS_SERVICES = [
    "Payment Gateway",
    "Core Banking",
    "Customer Portal",
    "Identity Provider",
    "Internal Operations",
]


def generate_synthetic_dataset(n_samples: int = 1200, seed: int = 42) -> pd.DataFrame:
    """Generate labeled synthetic cybersecurity risk observation records."""
    np.random.seed(seed)

    # 1. CVSS: mixture of medium (5.5, std 1.2) and critical (8.5, std 1.0)
    is_high_cvss = np.random.rand(n_samples) > 0.45
    cvss_low = np.random.normal(5.5, 1.2, n_samples)
    cvss_high = np.random.normal(8.5, 0.9, n_samples)
    cvss = np.where(is_high_cvss, cvss_high, cvss_low)
    cvss = np.clip(np.round(cvss, 1), 0.0, 10.0)

    # 2. EPSS: log-logistic / beta heavily skewed to 0
    epss_raw = np.random.beta(0.4, 2.5, n_samples)
    # Boost EPSS if CVSS is high
    epss = np.where(cvss >= 7.5, np.clip(epss_raw * 1.5, 0.0, 0.99), epss_raw)
    epss = np.clip(np.round(epss, 3), 0.001, 0.999)

    # 3. KEV: correlated with high CVSS & high EPSS
    kev_prob = 0.05 + 0.55 * (epss > 0.40) + 0.30 * (cvss >= 8.5)
    kev_prob = np.clip(kev_prob, 0.02, 0.95)
    kev = (np.random.rand(n_samples) < kev_prob).astype(int)

    # 4. Internet exposed: ~40% of enterprise assets
    internet_exposed = (np.random.rand(n_samples) < 0.42).astype(int)

    # 5. Criticality
    criticality = np.random.choice(
        CRITICALITIES,
        size=n_samples,
        p=[0.20, 0.35, 0.30, 0.15],
    )

    # 6. Asset type
    asset_type = np.random.choice(
        ASSET_TYPES,
        size=n_samples,
        p=[0.20, 0.25, 0.20, 0.15, 0.10, 0.10],
    )

    # 7. Business service
    business_service = np.random.choice(
        BUSINESS_SERVICES,
        size=n_samples,
        p=[0.25, 0.25, 0.20, 0.15, 0.15],
    )

    # Ground truth latent risk function
    criticality_weights = {"Critical": 1.6, "High": 0.9, "Medium": 0.0, "Low": -0.8}
    asset_weights = {
        "Database": 1.2,
        "Application Gateway": 0.8,
        "API Service": 0.6,
        "Web Server": 0.5,
        "Cloud Storage": 0.3,
        "Workstation": -0.7,
    }
    service_weights = {
        "Payment Gateway": 1.3,
        "Core Banking": 1.4,
        "Identity Provider": 1.0,
        "Customer Portal": 0.4,
        "Internal Operations": -0.6,
    }

    # Calculate logit
    crit_w = np.array([criticality_weights[c] for c in criticality])
    asset_w = np.array([asset_weights[a] for a in asset_type])
    serv_w = np.array([service_weights[s] for s in business_service])

    # Calibrated risk formula + random noise
    noise = np.random.normal(0, 0.45, n_samples)
    logit = (
        -4.2
        + 0.42 * cvss
        + 2.8 * epss
        + 1.7 * kev
        + 1.3 * internet_exposed
        + crit_w
        + asset_w
        + serv_w
        + noise
    )

    prob = 1.0 / (1.0 + np.exp(-logit))
    high_impact_event = (prob >= 0.50).astype(int)

    df = pd.DataFrame(
        {
            "cvss": cvss,
            "epss": epss,
            "kev": kev,
            "internet_exposed": internet_exposed,
            "criticality": criticality,
            "asset_type": asset_type,
            "business_service": business_service,
            "high_impact_event": high_impact_event,
        }
    )

    return df


def train_and_save_model(
    model_path: Optional[Path] = None,
    dataset_path: Optional[Path] = None,
) -> dict:
    """Train the Logistic Regression model and serialize artifact.

    Args:
        model_path: Destination for the serialized artifact. Defaults to MODEL_PATH.
        dataset_path: Destination for the generated training CSV. Defaults to DATASET_PATH.

    Both default to the module-level repository paths, so normal application usage
    is unchanged. Callers that pass explicit paths (e.g. tests using a temporary
    directory) write only to those paths and never touch the repository copies.
    """
    target_model_path = Path(model_path) if model_path is not None else MODEL_PATH
    target_dataset_path = Path(dataset_path) if dataset_path is not None else DATASET_PATH

    target_dataset_path.parent.mkdir(parents=True, exist_ok=True)
    target_model_path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_synthetic_dataset(n_samples=1200, seed=42)
    df.to_csv(target_dataset_path, index=False)

    features = [
        "cvss",
        "epss",
        "kev",
        "internet_exposed",
        "criticality",
        "asset_type",
        "business_service",
    ]
    target = "high_impact_event"

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    numeric_cols = ["cvss", "epss", "kev", "internet_exposed"]
    categorical_cols = ["criticality", "asset_type", "business_service"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols),
        ]
    )

    clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", clf),
        ]
    )

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    auc = float(roc_auc_score(y_test, y_prob))

    # Save model artifact and metadata
    artifact = {
        "pipeline": pipeline,
        "features": features,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "model_version": ML_MODEL_VERSION,
        "metrics": {"accuracy": round(acc, 4), "roc_auc": round(auc, 4)},
    }

    joblib.dump(artifact, target_model_path)

    return artifact


if __name__ == "__main__":
    meta = train_and_save_model()
    print(
        f"Trained {meta['model_version']} - Accuracy: {meta['metrics']['accuracy']}, ROC-AUC: {meta['metrics']['roc_auc']}"
    )
