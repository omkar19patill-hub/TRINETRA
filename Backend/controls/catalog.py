"""Reusable Security Controls Catalog

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Contains standard enterprise security controls mapping directly to cybersecurity
engineering standards (NIST SP 800-53, CIS Controls v8, ISO 27001):
1. MFA: Phishing-Resistant Multi-Factor Authentication
2. EDR: Next-Gen Endpoint Detection and Response
3. Vulnerability Patching: Automated Vulnerability & Patch Management
4. Backup and Recovery: Immutable Air-Gapped Cloud Backups
5. WAF: Cloud Web Application Firewall
6. PAM: Privileged Access Management
7. Security Monitoring: 24/7 SIEM & Managed SOC Operations
8. Security Awareness Training: Gamified Phishing & Awareness Simulation
9. ZTNA: Zero Trust Network Access & Micro-Segmentation
10. Data Encryption: Transparent Database & Field-Level Encryption
"""

from typing import Dict, List, Optional
from .models import RiskReductionEffect, SecurityControl


_CATALOG: List[SecurityControl] = [
    SecurityControl(
        control_id="CTRL-MFA",
        control_name="Multi-Factor Authentication",
        description="Enforces FIDO2 / WebAuthn hardware token multi-factor authentication across enterprise identity providers.",
        category="Identity & Access",
        implementation_cost=350000.0,
        annual_cost=75000.0,
        risk_reduction_effect=RiskReductionEffect(
            epss_multiplier=0.45,
            likelihood_mitigation_factor=0.35,
            cvss_reduction=1.0,
        ),
        applicable_asset_types=["web_application", "api_gateway", "workstation", "cloud_server", "internal_network", "all"],
        required_dependencies=[],
        implementation_time=14,
        confidence=0.95,
    ),
    SecurityControl(
        control_id="CTRL-EDR",
        control_name="Endpoint Detection and Response",
        description="Continuous behavioral monitoring, machine-learning anomaly detection, automated host isolation, and rapid live triage.",
        category="Endpoint Security",
        implementation_cost=600000.0,
        annual_cost=120000.0,
        risk_reduction_effect=RiskReductionEffect(
            likelihood_mitigation_factor=0.30,
            downtime_reduction_pct=0.40,
            incident_response_reduction_pct=0.35,
        ),
        applicable_asset_types=["workstation", "cloud_server", "database", "internal_network", "all"],
        required_dependencies=[],
        implementation_time=21,
        confidence=0.92,
    ),
    SecurityControl(
        control_id="CTRL-PATCH",
        control_name="Vulnerability Patching",
        description="Automated vulnerability discovery, prioritized remediation workflow, virtual patching, and emergency zero-day patch pipelines.",
        category="Vulnerability Management",
        implementation_cost=400000.0,
        annual_cost=90000.0,
        risk_reduction_effect=RiskReductionEffect(
            cvss_reduction=4.0,
            epss_multiplier=0.20,
            kev_neutralized=True,
            likelihood_mitigation_factor=0.25,
        ),
        applicable_asset_types=["web_application", "api_gateway", "workstation", "cloud_server", "database", "all"],
        required_dependencies=[],
        implementation_time=28,
        confidence=0.94,
    ),
    SecurityControl(
        control_id="CTRL-BACKUP",
        control_name="Backup and Recovery",
        description="Immutable write-once-read-many (WORM) air-gapped snapshots with automated cross-region recovery orchestration.",
        category="Data Resilience",
        implementation_cost=450000.0,
        annual_cost=80000.0,
        risk_reduction_effect=RiskReductionEffect(
            downtime_reduction_pct=0.65,
            recovery_cost_reduction_pct=0.55,
        ),
        applicable_asset_types=["cloud_server", "database", "workstation", "api_gateway", "web_application", "all"],
        required_dependencies=[],
        implementation_time=18,
        confidence=0.96,
    ),
    SecurityControl(
        control_id="CTRL-WAF",
        control_name="Web Application Firewall",
        description="Edge Layer 7 proxy with automated OWASP Top 10 mitigation, API schema enforcement, bot defense, and rate-limiting.",
        category="Application Security",
        implementation_cost=500000.0,
        annual_cost=110000.0,
        risk_reduction_effect=RiskReductionEffect(
            exposure_mitigation=True,
            likelihood_mitigation_factor=0.30,
            epss_multiplier=0.50,
        ),
        applicable_asset_types=["web_application", "api_gateway"],
        required_dependencies=[],
        implementation_time=20,
        confidence=0.91,
    ),
    SecurityControl(
        control_id="CTRL-PAM",
        control_name="Privileged Access Management",
        description="Just-in-time credential vaulting, ephemeral administrative privileges, session recording, and credential rotation.",
        category="Identity & Access",
        implementation_cost=700000.0,
        annual_cost=150000.0,
        risk_reduction_effect=RiskReductionEffect(
            likelihood_mitigation_factor=0.30,
            regulatory_reduction_pct=0.30,
            customer_impact_reduction_pct=0.30,
        ),
        applicable_asset_types=["cloud_server", "database", "internal_network", "workstation", "all"],
        required_dependencies=["CTRL-MFA"],
        implementation_time=35,
        confidence=0.89,
    ),
    SecurityControl(
        control_id="CTRL-SIEM",
        control_name="Security Monitoring",
        description="Centralized cloud-native SIEM with real-time log correlation, automated SOAR playbooks, and 24/7 security analyst coverage.",
        category="Security Operations",
        implementation_cost=1200000.0,
        annual_cost=300000.0,
        risk_reduction_effect=RiskReductionEffect(
            downtime_reduction_pct=0.35,
            incident_response_reduction_pct=0.45,
            customer_impact_reduction_pct=0.30,
            likelihood_mitigation_factor=0.15,
        ),
        applicable_asset_types=["cloud_server", "database", "workstation", "web_application", "api_gateway", "internal_network", "all"],
        required_dependencies=["CTRL-EDR"],
        implementation_time=60,
        confidence=0.90,
    ),
    SecurityControl(
        control_id="CTRL-TRAIN",
        control_name="Security Awareness Training",
        description="Continuous adaptive security culture training, simulated spear-phishing campaigns, and executive threat awareness drills.",
        category="Human Layer",
        implementation_cost=150000.0,
        annual_cost=40000.0,
        risk_reduction_effect=RiskReductionEffect(
            likelihood_mitigation_factor=0.15,
            epss_multiplier=0.80,
        ),
        applicable_asset_types=["workstation", "internal_network", "all"],
        required_dependencies=[],
        implementation_time=7,
        confidence=0.85,
    ),
    SecurityControl(
        control_id="CTRL-ZTNA",
        control_name="Zero Trust Network Access",
        description="Software-defined micro-segmentation, identity-aware secure application proxies, and continuous device health validation.",
        category="Network Security",
        implementation_cost=1000000.0,
        annual_cost=220000.0,
        risk_reduction_effect=RiskReductionEffect(
            exposure_mitigation=True,
            likelihood_mitigation_factor=0.35,
            regulatory_reduction_pct=0.25,
        ),
        applicable_asset_types=["cloud_server", "database", "workstation", "internal_network", "all"],
        required_dependencies=["CTRL-MFA"],
        implementation_time=45,
        confidence=0.91,
    ),
    SecurityControl(
        control_id="CTRL-ENCRYPT",
        control_name="Data Encryption",
        description="AES-256 transparent database encryption, cryptographic envelope key management with Hardware Security Modules (HSM).",
        category="Data Protection",
        implementation_cost=550000.0,
        annual_cost=95000.0,
        risk_reduction_effect=RiskReductionEffect(
            regulatory_reduction_pct=0.70,
            customer_impact_reduction_pct=0.60,
            recovery_cost_reduction_pct=0.20,
        ),
        applicable_asset_types=["database", "cloud_server"],
        required_dependencies=[],
        implementation_time=30,
        confidence=0.95,
    ),
]


def get_all_controls() -> List[SecurityControl]:
    """Retrieve complete catalog of standard security controls."""
    return list(_CATALOG)


def get_control_by_id(control_id: str) -> Optional[SecurityControl]:
    """Find a control by unique identifier (case-insensitive)."""
    norm = control_id.strip().upper()
    for ctrl in _CATALOG:
        if ctrl.control_id.upper() == norm:
            return ctrl
    return None


def get_controls_by_ids(control_ids: List[str]) -> List[SecurityControl]:
    """Retrieve multiple controls matching a list of identifiers."""
    result = []
    for cid in control_ids:
        c = get_control_by_id(cid)
        if c:
            result.append(c)
    return result


def get_controls_by_category(category: str) -> List[SecurityControl]:
    """Filter controls matching a specific category (case-insensitive)."""
    norm = category.strip().lower()
    return [c for c in _CATALOG if c.category.lower() == norm]


def get_controls_for_asset_type(asset_type: str) -> List[SecurityControl]:
    """Filter controls applicable to a specific asset type."""
    norm = asset_type.strip().lower()
    return [
        c for c in _CATALOG
        if "all" in [t.lower() for t in c.applicable_asset_types]
        or norm in [t.lower() for t in c.applicable_asset_types]
    ]
