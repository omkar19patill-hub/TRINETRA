"""In-Memory Store & Registry for Cyber Risk Investment Optimizations

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105
DEV 2: Decision Intelligence Layer

Provides storage, querying, and pre-seeded benchmark optimizations for explainability,
opportunity cost evaluation, and marginal budget sensitivity.
"""

import threading
from typing import Dict, List, Optional
from datetime import datetime, timezone
from .schemas import CandidateControl, OptimizationResult


_LOCK = threading.Lock()
_ACTUAL_OPTIMIZATION_STORE: Dict[str, OptimizationResult] = {}
_BENCHMARK_OPTIMIZATION_STORE: Dict[str, OptimizationResult] = {}
# Backwards-compatible reference alias
_OPTIMIZATION_STORE = _ACTUAL_OPTIMIZATION_STORE


def _get_benchmark_controls() -> List[CandidateControl]:
    """Return standard enterprise benchmark candidate controls with realistic metrics."""
    return [
        CandidateControl(
            control_id="CTRL-MFA",
            name="Phishing-Resistant MFA",
            cost=350000.0,
            risk_reduction=680000.0,
            workforce_hours=80.0,
            implementation_days=14,
            applicable_assets=["AST-001", "AST-002", "AST-003", "AST-004"],
            critical_assets_covered=4,
            category="Identity & Access",
            description="Enforces FIDO2 hardware token multi-factor authentication across all identity providers.",
        ),
        CandidateControl(
            control_id="CTRL-EDR",
            name="Next-Gen EDR",
            cost=600000.0,
            risk_reduction=1050000.0,
            workforce_hours=140.0,
            implementation_days=21,
            applicable_assets=["AST-001", "AST-002", "AST-003", "AST-005", "AST-006"],
            critical_assets_covered=5,
            category="Endpoint Security",
            description="Continuous behavioral endpoint monitoring, automated isolation, and threat hunting.",
        ),
        CandidateControl(
            control_id="CTRL-PATCH",
            name="Automated Patch Management",
            cost=400000.0,
            risk_reduction=720000.0,
            workforce_hours=100.0,
            implementation_days=28,
            applicable_assets=["AST-001", "AST-002", "AST-003", "AST-004"],
            critical_assets_covered=4,
            category="Vulnerability Management",
            description="Automates staging, compatibility testing, and rapid zero-day patching cycles.",
        ),
        CandidateControl(
            control_id="CTRL-BACKUP",
            name="Immutable Cloud Backups",
            cost=450000.0,
            risk_reduction=800000.0,
            workforce_hours=90.0,
            implementation_days=18,
            applicable_assets=["AST-001", "AST-002", "AST-003", "AST-005", "AST-006"],
            critical_assets_covered=5,
            category="Data Resilience",
            description="Write-once-read-many (WORM) air-gapped snapshots for rapid ransomware recovery.",
        ),
        CandidateControl(
            control_id="CTRL-WAF",
            name="Cloud Web Application Firewall",
            cost=500000.0,
            risk_reduction=650000.0,
            workforce_hours=110.0,
            implementation_days=20,
            applicable_assets=["AST-001", "AST-002", "AST-004"],
            critical_assets_covered=3,
            category="Application Security",
            description="L7 DDoS mitigation, OWASP Top 10 virtual patching, and bot management.",
        ),
        CandidateControl(
            control_id="CTRL-PAM",
            name="Privileged Access Management",
            cost=700000.0,
            risk_reduction=750000.0,
            workforce_hours=160.0,
            implementation_days=35,
            applicable_assets=["AST-001", "AST-002", "AST-005"],
            critical_assets_covered=3,
            category="Identity & Access",
            description="Just-in-time credential vaulting, session recording, and credential rotation.",
        ),
        CandidateControl(
            control_id="CTRL-SIEM",
            name="SIEM & 24/7 SOC Triage",
            cost=1200000.0,
            risk_reduction=1100000.0,
            workforce_hours=220.0,
            implementation_days=60,
            applicable_assets=["AST-001", "AST-002", "AST-003", "AST-004"],
            critical_assets_covered=4,
            category="Security Operations",
            description="Centralized log aggregation, real-time correlation rules, and managed SOC alerting.",
        ),
        CandidateControl(
            control_id="CTRL-TRAIN",
            name="Security Awareness & Phishing Simulation",
            cost=150000.0,
            risk_reduction=220000.0,
            workforce_hours=30.0,
            implementation_days=7,
            applicable_assets=["AST-003", "AST-004"],
            critical_assets_covered=2,
            category="Human Layer",
            description="Gamified employee training modules, simulated phishing campaigns, and reporting.",
        ),
        CandidateControl(
            control_id="CTRL-ZTNA",
            name="Zero Trust Network Architecture",
            cost=1000000.0,
            risk_reduction=900000.0,
            workforce_hours=200.0,
            implementation_days=45,
            applicable_assets=["AST-001", "AST-002", "AST-005", "AST-006"],
            critical_assets_covered=4,
            category="Network Security",
            description="Micro-segmentation, identity-aware reverse proxies, and continuous context validation.",
        ),
        CandidateControl(
            control_id="CTRL-ENCRYPT",
            name="Database & Field-Level Encryption",
            cost=550000.0,
            risk_reduction=600000.0,
            workforce_hours=130.0,
            implementation_days=30,
            applicable_assets=["AST-001", "AST-002", "AST-003"],
            critical_assets_covered=3,
            category="Data Protection",
            description="AES-256 transparent database encryption with Hardware Security Module (HSM) key custody.",
        ),
    ]


def seed_benchmark_optimizations() -> None:
    """Initialize benchmark enterprise optimization instances strictly into benchmark storage."""
    benchmark_controls = _get_benchmark_controls()
    
    primary_benchmark = OptimizationResult(
        optimization_id="OPT-BENCHMARK-001",
        title="Enterprise Critical Infrastructure Cyber Investment Portfolio",
        baseline_risk=5000000.0,
        budget_limit=1800000.0,
        currency="INR",
        selected_portfolio_id="portfolio-balanced-roi",
        candidate_controls=benchmark_controls,
        created_at=datetime.now(timezone.utc).isoformat(),
        data_source="benchmark",
        is_benchmark=True,
        model_version="OPT-BENCHMARK-1.0",
        assessment_id="AST-BENCHMARK-001",
    )

    enterprise_scenario = OptimizationResult(
        optimization_id="OPT-ENTERPRISE-001",
        title="Tier-1 Banking Financial Sector Risk Optimization",
        baseline_risk=8500000.0,
        budget_limit=2500000.0,
        currency="INR",
        selected_portfolio_id="portfolio-balanced-roi",
        candidate_controls=benchmark_controls,
        created_at=datetime.now(timezone.utc).isoformat(),
        data_source="benchmark",
        is_benchmark=True,
        model_version="OPT-BENCHMARK-1.0",
        assessment_id="AST-ENTERPRISE-001",
    )

    with _LOCK:
        _BENCHMARK_OPTIMIZATION_STORE["OPT-BENCHMARK-001"] = primary_benchmark
        _BENCHMARK_OPTIMIZATION_STORE["opt-benchmark-001"] = primary_benchmark
        _BENCHMARK_OPTIMIZATION_STORE["OPT-2026-001"] = primary_benchmark
        _BENCHMARK_OPTIMIZATION_STORE["opt-default-001"] = primary_benchmark
        _BENCHMARK_OPTIMIZATION_STORE["OPT-ENTERPRISE-001"] = enterprise_scenario
        _BENCHMARK_OPTIMIZATION_STORE["opt-enterprise-001"] = enterprise_scenario


def get_optimization(optimization_id: str, demo_mode: bool = False) -> Optional[OptimizationResult]:
    """Retrieve an optimization result by identifier.
    
    Checks actual optimizer store first. If not found:
    - If demo_mode is True, returns matching benchmark data (or default benchmark).
    - If demo_mode is False, only returns if explicitly referencing a benchmark identifier
      (e.g. for unit and integration test fixtures), and labels it as benchmark data.
      Never silently replaces an actual optimization run ID with benchmark data.
    """
    clean_id = (optimization_id or "").strip()
    with _LOCK:
        # 1. Search actual optimizer results
        if clean_id in _ACTUAL_OPTIMIZATION_STORE:
            return _ACTUAL_OPTIMIZATION_STORE[clean_id]
        for k, v in _ACTUAL_OPTIMIZATION_STORE.items():
            if k.lower() == clean_id.lower():
                return v

        # 2. Check benchmark store
        is_explicit_benchmark = (
            clean_id.upper().startswith("OPT-BENCHMARK")
            or clean_id.upper().startswith("OPT-ENTERPRISE")
            or clean_id.upper() in ["OPT-2026-001", "OPT-DEFAULT-001"]
        )

        if demo_mode:
            # Explicit demo mode requested: allow benchmark fallback
            if clean_id in _BENCHMARK_OPTIMIZATION_STORE:
                return _BENCHMARK_OPTIMIZATION_STORE[clean_id]
            for k, v in _BENCHMARK_OPTIMIZATION_STORE.items():
                if k.lower() == clean_id.lower():
                    return v
            return _BENCHMARK_OPTIMIZATION_STORE.get("OPT-BENCHMARK-001")

        if is_explicit_benchmark:
            # Caller explicitly requested a benchmark test fixture ID
            return (
                _BENCHMARK_OPTIMIZATION_STORE.get(clean_id)
                or _BENCHMARK_OPTIMIZATION_STORE.get(clean_id.upper())
                or _BENCHMARK_OPTIMIZATION_STORE.get(clean_id.lower())
            )

        # Neither actual nor explicit demo mode: do not silently fall back
        return None


def save_optimization(optimization: OptimizationResult, is_benchmark: bool = False) -> None:
    """Save or update an optimization result in the appropriate store."""
    with _LOCK:
        if is_benchmark or optimization.is_benchmark or optimization.data_source == "benchmark":
            _BENCHMARK_OPTIMIZATION_STORE[optimization.optimization_id] = optimization
        else:
            _ACTUAL_OPTIMIZATION_STORE[optimization.optimization_id] = optimization
            # Keep alias in sync for backward compatibility
            _OPTIMIZATION_STORE[optimization.optimization_id] = optimization


def list_optimizations(demo_mode: bool = False) -> List[OptimizationResult]:
    """Return stored optimization results. Returns actual optimizations by default, or benchmark if demo_mode is True."""
    with _LOCK:
        seen = set()
        results = []
        source_store = _ACTUAL_OPTIMIZATION_STORE if (not demo_mode and _ACTUAL_OPTIMIZATION_STORE) else {**_BENCHMARK_OPTIMIZATION_STORE, **_ACTUAL_OPTIMIZATION_STORE}
        for opt in source_store.values():
            if opt.optimization_id not in seen:
                seen.add(opt.optimization_id)
                results.append(opt)
        return results


def store_count() -> int:
    """Return count of registered unique optimizations."""
    return len(list_optimizations(demo_mode=True))


# Seed benchmark instances in isolated benchmark storage immediately on module import
seed_benchmark_optimizations()
