"""Core Risk Engine Orchestrator

TRINETRA - SIH 2026

Coordinates risk quantification across scoring, impact lookup, and driver generation.
STRICT REQUIREMENT: This module is pure Python and completely decoupled from FastAPI,
HTTP requests, and database layers, enabling direct reuse by batch pipelines,
message consumers, or API endpoints.
"""

from typing import Any, Dict, Union
from .constants import MODEL_VERSION, MODEL_TYPE
from .schemas import (
    RiskCalculationRequest,
    RiskCalculationResponse,
    CalculationBreakdown,
    ModelInfo,
)
from .scoring import (
    normalize_cvss,
    calculate_likelihood,
    calculate_impact,
    calculate_risk_score,
    get_risk_level,
)
from .drivers import generate_risk_drivers


def calculate_risk(
    input_data: Union[RiskCalculationRequest, Dict[str, Any]]
) -> RiskCalculationResponse:
    """Orchestrate the end-to-end deterministic risk calculation.

    Workflow:
        1. Validate input against RiskCalculationRequest schema (if dict provided)
        2. Normalize CVSS [0.0 - 10.0] -> [0.0 - 1.0]
        3. Compute Likelihood from normalized CVSS, EPSS, KEV signal, and Exposure signal
        4. Look up business Impact multiplier from asset criticality
        5. Calculate overall Risk Score = Likelihood * Impact * 100
        6. Determine categorical Risk Level (CRITICAL, HIGH, MEDIUM, LOW)
        7. Evaluate explainable Risk Drivers
        8. Package step-by-step calculation breakdown and model governance info

    Args:
        input_data: Validated RiskCalculationRequest instance or raw dictionary

    Returns:
        RiskCalculationResponse populated with all score dimensions and breakdown.
    """
    if isinstance(input_data, dict):
        validated_request = RiskCalculationRequest(**input_data)
    elif isinstance(input_data, RiskCalculationRequest):
        validated_request = input_data
    else:
        raise TypeError(
            f"Expected RiskCalculationRequest or dict, got {type(input_data).__name__}"
        )

    # 1. Normalize CVSS
    cvss_normalized = normalize_cvss(validated_request.cvss)

    # 2. Calculate Likelihood & factor contributions
    likelihood, breakdown_dict = calculate_likelihood(
        cvss_normalized=cvss_normalized,
        epss=validated_request.epss,
        kev=validated_request.kev,
        internet_exposed=validated_request.internet_exposed,
    )

    # 3. Calculate Impact
    criticality_str = (
        validated_request.criticality.value
        if hasattr(validated_request.criticality, "value")
        else str(validated_request.criticality)
    )
    impact = calculate_impact(criticality_str)

    # 4. Calculate Final Risk Score
    risk_score = calculate_risk_score(likelihood=likelihood, impact=impact)

    # 5. Classify Risk Level
    risk_level = get_risk_level(risk_score)

    # 6. Generate Risk Drivers for explainability
    drivers = generate_risk_drivers(
        cvss=validated_request.cvss,
        epss=validated_request.epss,
        kev=validated_request.kev,
        internet_exposed=validated_request.internet_exposed,
        criticality=criticality_str,
    )

    # 7. Construct Calculation Breakdown
    calculation_breakdown = CalculationBreakdown(**breakdown_dict)

    # 8. Model Governance Info
    model_info = ModelInfo(
        version=MODEL_VERSION,
        type=MODEL_TYPE,
    )

    # 9. Assemble Response
    return RiskCalculationResponse(
        asset_id=validated_request.asset_id,
        cve_id=validated_request.cve_id,
        likelihood=likelihood,
        impact=impact,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_drivers=drivers,
        calculation=calculation_breakdown,
        model=model_info,
    )
