"""Explainable Risk Drivers Generator

TRINETRA - SIH 2026

Generates human-readable, deterministic explanations ("Risk Drivers") that justify
why a risk score achieved a specific tier. Designed as an extensible rule-based system
so new domain rules can easily be registered in future SIH phases.
"""

from typing import Callable, List, NamedTuple
from .constants import CVSS_DRIVER_THRESHOLD, EPSS_DRIVER_THRESHOLD


class DriverRule(NamedTuple):
    """Rule definition for risk driver generation."""
    name: str
    description: str
    evaluator: Callable[..., bool]


def _is_critical_cvss(cvss: float, **kwargs) -> bool:
    return cvss >= CVSS_DRIVER_THRESHOLD


def _is_high_epss(epss: float, **kwargs) -> bool:
    return epss >= EPSS_DRIVER_THRESHOLD


def _is_known_exploited(kev: bool, **kwargs) -> bool:
    return bool(kev)


def _is_internet_exposed(internet_exposed: bool, **kwargs) -> bool:
    return bool(internet_exposed)


def _is_critical_business_asset(criticality: str, **kwargs) -> bool:
    return criticality == "Critical"


# Default registered explainability rules
# Extensible list: add new DriverRule instances here to register future risk factors.
DEFAULT_DRIVER_RULES: List[DriverRule] = [
    DriverRule(
        name="Critical CVSS",
        description=f"Vulnerability has a base CVSS score >= {CVSS_DRIVER_THRESHOLD}",
        evaluator=_is_critical_cvss,
    ),
    DriverRule(
        name="High exploitation probability",
        description=f"EPSS exploit probability exceeds {EPSS_DRIVER_THRESHOLD}",
        evaluator=_is_high_epss,
    ),
    DriverRule(
        name="Known exploited vulnerability",
        description="Listed in CISA Known Exploited Vulnerabilities (KEV) catalog",
        evaluator=_is_known_exploited,
    ),
    DriverRule(
        name="Internet exposed asset",
        description="Asset is directly reachable from public networks",
        evaluator=_is_internet_exposed,
    ),
    DriverRule(
        name="Critical business asset",
        description="Asset tier is rated Critical for enterprise operations",
        evaluator=_is_critical_business_asset,
    ),
]


def generate_risk_drivers(
    cvss: float,
    epss: float,
    kev: bool,
    internet_exposed: bool,
    criticality: str,
    rules: List[DriverRule] = DEFAULT_DRIVER_RULES,
) -> List[str]:
    """Evaluate context against explainability rules to generate active risk drivers.

    Args:
        cvss: Base CVSS score [0.0 - 10.0]
        epss: EPSS exploitation probability [0.0 - 1.0]
        kev: Whether CVE is in CISA KEV catalog
        internet_exposed: Whether asset is internet exposed
        criticality: Asset business criticality string ("Critical", "High", etc.)
        rules: List of DriverRule instances to evaluate (defaults to DEFAULT_DRIVER_RULES)

    Returns:
        List of human-readable risk driver strings explaining the risk factors.
    """
    context = {
        "cvss": cvss,
        "epss": epss,
        "kev": kev,
        "internet_exposed": internet_exposed,
        "criticality": criticality,
    }

    active_drivers: List[str] = []
    for rule in rules:
        try:
            if rule.evaluator(**context):
                active_drivers.append(rule.name)
        except Exception:
            # Keep driver generation resilient: skip failing evaluator without crashing
            continue

    return active_drivers
