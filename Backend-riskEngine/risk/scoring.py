"""Deterministic Scoring Logic for the TRINETRA Risk Engine

TRINETRA - SIH 2026

Contains pure, deterministic mathematical functions for:
- CVSS score normalization
- Likelihood calculation with factor contributions
- Asset impact lookup
- Final Risk Score computation (clamped [0 - 100])
- Risk Level categorization
"""

from typing import Any, Dict, Tuple
from .constants import (
    CVSS_WEIGHT,
    EPSS_WEIGHT,
    KEV_WEIGHT,
    EXPOSURE_WEIGHT,
    CRITICALITY_IMPACT,
    RISK_LEVEL_THRESHOLDS,
    MIN_RISK_SCORE,
    MAX_RISK_SCORE,
    SCORE_DECIMAL_PLACES,
    CALCULATION_DECIMAL_PLACES,
)


def normalize_cvss(cvss: float) -> float:
    """Normalize CVSS score (0.0 - 10.0) to a standard scale of [0.0 - 1.0].

    Examples:
        normalize_cvss(10.0) -> 1.0
        normalize_cvss(5.0)  -> 0.5
        normalize_cvss(0.0)  -> 0.0
    """
    normalized = cvss / 10.0
    return round(max(0.0, min(1.0, normalized)), CALCULATION_DECIMAL_PLACES)


def calculate_likelihood(
    cvss_normalized: float,
    epss: float,
    kev: bool,
    internet_exposed: bool,
) -> Tuple[float, Dict[str, Any]]:
    """Calculate the deterministic exploitation likelihood.

    Formula:
        Likelihood = (CVSS_WEIGHT * CVSS_normalized)
                   + (EPSS_WEIGHT * EPSS)
                   + (KEV_WEIGHT * KEV_signal)
                   + (EXPOSURE_WEIGHT * Exposure_signal)

    Signals:
        KEV_signal:      1 if kev is True, else 0
        Exposure_signal: 1 if internet_exposed is True, else 0

    Returns:
        tuple of:
        - total likelihood float (clamped [0.0 - 1.0], rounded)
        - breakdown dictionary of signals and individual contributions
    """
    kev_signal = 1 if kev else 0
    exposure_signal = 1 if internet_exposed else 0

    cvss_contribution = round(CVSS_WEIGHT * cvss_normalized, CALCULATION_DECIMAL_PLACES)
    epss_contribution = round(EPSS_WEIGHT * epss, CALCULATION_DECIMAL_PLACES)
    kev_contribution = round(KEV_WEIGHT * kev_signal, CALCULATION_DECIMAL_PLACES)
    exposure_contribution = round(EXPOSURE_WEIGHT * exposure_signal, CALCULATION_DECIMAL_PLACES)

    raw_likelihood = (
        cvss_contribution
        + epss_contribution
        + kev_contribution
        + exposure_contribution
    )
    clamped_likelihood = max(0.0, min(1.0, raw_likelihood))
    likelihood = round(clamped_likelihood, CALCULATION_DECIMAL_PLACES)

    breakdown = {
        "cvss_normalized": cvss_normalized,
        "epss": round(epss, CALCULATION_DECIMAL_PLACES),
        "kev_signal": kev_signal,
        "exposure_signal": exposure_signal,
        "cvss_contribution": cvss_contribution,
        "epss_contribution": epss_contribution,
        "kev_contribution": kev_contribution,
        "exposure_contribution": exposure_contribution,
    }

    return likelihood, breakdown


def calculate_impact(criticality: str) -> float:
    """Determine deterministic business impact from asset criticality tier.

    Mapping:
        Critical -> 1.00
        High     -> 0.75
        Medium   -> 0.50
        Low      -> 0.25

    Args:
        criticality: Business criticality string ("Critical", "High", etc.)

    Returns:
        float impact factor in [0.0 - 1.0]
    """
    if criticality not in CRITICALITY_IMPACT:
        raise ValueError(
            f"Invalid criticality '{criticality}'. Must be one of: {list(CRITICALITY_IMPACT.keys())}"
        )
    return CRITICALITY_IMPACT[criticality]


def calculate_risk_score(likelihood: float, impact: float) -> float:
    """Compute the deterministic overall Risk Score.

    Formula:
        Risk Score = Likelihood * Impact * 100

    Score is clamped within [0.0, 100.0] and rounded to 2 decimal places.

    Example:
        Likelihood = 0.895, Impact = 1.0
        Risk Score = 0.895 * 1.0 * 100 = 89.5
    """
    raw_score = likelihood * impact * 100.0
    clamped_score = max(MIN_RISK_SCORE, min(MAX_RISK_SCORE, raw_score))
    return round(clamped_score, SCORE_DECIMAL_PLACES)


def get_risk_level(score: float) -> str:
    """Classify the Risk Score into a categorical Risk Level tier.

    Prototype Thresholds:
        75 - 100 -> CRITICAL
        50 - 74  -> HIGH
        25 - 49  -> MEDIUM
        0  - 24  -> LOW

    Args:
        score: Risk score between 0.0 and 100.0

    Returns:
        One of 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    """
    for threshold, level in RISK_LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return "LOW"
