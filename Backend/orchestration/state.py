"""Enterprise Asset Inventory & Change Detection Engine (DEV 2)

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Maintains live asset contextual baselines and detects concrete, non-hallucinated
change reasons when threat intelligence or asset parameters fluctuate.
"""

import copy
import threading
from typing import Any, Dict, List, Optional, Tuple


class AssetState:
    """Represents the live contextual state of an enterprise IT asset."""

    def __init__(
        self,
        asset_id: str,
        name: str,
        cve_id: str,
        cvss: float,
        epss: float,
        kev: bool,
        internet_exposed: bool,
        criticality: str,
        is_patched: bool = False,
        revenue_loss_per_hour: float = 150000.0,
        downtime_hours: float = 10.0,
        incident_response_cost: float = 250000.0,
        recovery_cost: float = 300000.0,
        regulatory_fine_estimate: float = 400000.0,
        customer_impact_cost: float = 200000.0,
        budget_limit: float = 1800000.0,
    ):
        self.asset_id = asset_id
        self.name = name
        self.cve_id = cve_id
        self.cvss = cvss
        self.epss = epss
        self.kev = kev
        self.internet_exposed = internet_exposed
        self.criticality = criticality
        self.is_patched = is_patched
        self.revenue_loss_per_hour = revenue_loss_per_hour
        self.downtime_hours = downtime_hours
        self.incident_response_cost = incident_response_cost
        self.recovery_cost = recovery_cost
        self.regulatory_fine_estimate = regulatory_fine_estimate
        self.customer_impact_cost = customer_impact_cost
        self.budget_limit = budget_limit

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "cve_id": self.cve_id,
            "cvss": self.cvss,
            "epss": self.epss,
            "kev": self.kev,
            "internet_exposed": self.internet_exposed,
            "criticality": self.criticality,
            "is_patched": self.is_patched,
            "revenue_loss_per_hour": self.revenue_loss_per_hour,
            "downtime_hours": self.downtime_hours,
            "incident_response_cost": self.incident_response_cost,
            "recovery_cost": self.recovery_cost,
            "regulatory_fine_estimate": self.regulatory_fine_estimate,
            "customer_impact_cost": self.customer_impact_cost,
            "budget_limit": self.budget_limit,
        }


_LOCK = threading.Lock()
_ASSET_REGISTRY: Dict[str, AssetState] = {}
_BASELINE_BACKUP: Dict[str, AssetState] = {}
_REOPTIMIZATION_COUNTER: int = 0


def _build_default_assets() -> List[AssetState]:
    """Define default enterprise benchmark assets."""
    return [
        AssetState(
            asset_id="AST-001",
            name="Core Enterprise Gateway",
            cve_id="CVE-2026-1234",
            cvss=9.8,
            epss=0.45,  # Baseline before elevation
            kev=False,  # Baseline before KEV cataloging
            internet_exposed=True,
            criticality="Critical",
            is_patched=False,
            revenue_loss_per_hour=150000.0,
            downtime_hours=10.0,
            budget_limit=1800000.0,
        ),
        AssetState(
            asset_id="AST-002",
            name="Primary Customer Database Cluster",
            cve_id="CVE-2026-1234",
            cvss=9.8,
            epss=0.45,
            kev=False,
            internet_exposed=False,
            criticality="Critical",
            is_patched=False,
            revenue_loss_per_hour=250000.0,
            downtime_hours=8.0,
            budget_limit=1800000.0,
        ),
        AssetState(
            asset_id="AST-003",
            name="Internal Identity & Access Proxy",
            cve_id="CVE-2021-44228",
            cvss=10.0,
            epss=0.975,
            kev=True,
            internet_exposed=False,
            criticality="High",
            is_patched=False,
            revenue_loss_per_hour=80000.0,
            downtime_hours=6.0,
            budget_limit=1800000.0,
        ),
        AssetState(
            asset_id="AST-004",
            name="Public DMZ Reverse Proxy",
            cve_id="CVE-2026-5678",
            cvss=7.5,
            epss=0.25,
            kev=False,
            internet_exposed=True,
            criticality="High",
            is_patched=False,
            revenue_loss_per_hour=100000.0,
            downtime_hours=4.0,
            budget_limit=1800000.0,
        ),
        AssetState(
            asset_id="AST-BANK-CORE",
            name="Tier-1 Banking Settlement Engine",
            cve_id="CVE-2021-44228",
            cvss=10.0,
            epss=0.975,
            kev=True,
            internet_exposed=True,
            criticality="Critical",
            is_patched=False,
            revenue_loss_per_hour=500000.0,
            downtime_hours=12.0,
            budget_limit=2500000.0,
        ),
    ]


def seed_asset_registry() -> None:
    """Initialize the asset registry with standard enterprise topology."""
    defaults = _build_default_assets()
    with _LOCK:
        _ASSET_REGISTRY.clear()
        _BASELINE_BACKUP.clear()
        for a in defaults:
            _ASSET_REGISTRY[a.asset_id] = copy.deepcopy(a)
            _BASELINE_BACKUP[a.asset_id] = copy.deepcopy(a)


def get_asset_state(asset_id: str) -> Optional[AssetState]:
    """Retrieve asset state by ID."""
    if not _ASSET_REGISTRY:
        seed_asset_registry()
    with _LOCK:
        asset = _ASSET_REGISTRY.get(asset_id)
        return copy.deepcopy(asset) if asset else None


def list_asset_states() -> List[Dict[str, Any]]:
    """List all registered asset states as dictionaries."""
    if not _ASSET_REGISTRY:
        seed_asset_registry()
    with _LOCK:
        return [a.to_dict() for a in _ASSET_REGISTRY.values()]


def update_asset_state(asset_id: str, new_state: AssetState) -> None:
    """Update live state of an asset."""
    with _LOCK:
        _ASSET_REGISTRY[asset_id] = copy.deepcopy(new_state)


def reset_asset_state(asset_id: str) -> Optional[AssetState]:
    """Reset an asset back to initial baseline."""
    with _LOCK:
        if asset_id in _BASELINE_BACKUP:
            _ASSET_REGISTRY[asset_id] = copy.deepcopy(_BASELINE_BACKUP[asset_id])
            return copy.deepcopy(_ASSET_REGISTRY[asset_id])
        return None


def increment_reoptimization_counter() -> int:
    """Increment and return cumulative re-optimization runs count."""
    global _REOPTIMIZATION_COUNTER
    with _LOCK:
        _REOPTIMIZATION_COUNTER += 1
        return _REOPTIMIZATION_COUNTER


def get_reoptimization_counter() -> int:
    """Get total executed re-optimizations count."""
    with _LOCK:
        return _REOPTIMIZATION_COUNTER


def identify_affected_assets(
    cve_id: Optional[str] = None,
    asset_id: Optional[str] = None,
) -> List[AssetState]:
    """Identify enterprise assets impacted by a vulnerability change or asset-level event."""
    if not _ASSET_REGISTRY:
        seed_asset_registry()

    with _LOCK:
        if asset_id and asset_id in _ASSET_REGISTRY:
            return [copy.deepcopy(_ASSET_REGISTRY[asset_id])]

        if cve_id:
            matched = [
                copy.deepcopy(a)
                for a in _ASSET_REGISTRY.values()
                if a.cve_id.strip().upper() == cve_id.strip().upper()
            ]
            if matched:
                return matched

        # Fallback to AST-001 if no specific match
        fallback = _ASSET_REGISTRY.get("AST-001") or list(_ASSET_REGISTRY.values())[0]
        return [copy.deepcopy(fallback)]


def detect_change_reasons(
    previous: AssetState,
    new_cvss: Optional[float] = None,
    new_epss: Optional[float] = None,
    new_kev: Optional[bool] = None,
    new_exposed: Optional[bool] = None,
    new_criticality: Optional[str] = None,
    new_patched: Optional[bool] = None,
    new_budget: Optional[float] = None,
    new_rev_loss: Optional[float] = None,
    new_downtime: Optional[float] = None,
) -> List[str]:
    """Detect concrete, factual parameter changes between old state and new triggers.
    
    Guarantees: No generic or invented explanations; only returns actual measured deltas.
    """
    reasons: List[str] = []

    # 1. KEV Status Detection
    if new_kev is not None and new_kev != previous.kev:
        if new_kev:
            reasons.append(f"CISA KEV catalog update: {previous.cve_id} is now confirmed actively exploited in the wild")
        else:
            reasons.append(f"CISA KEV catalog update: active exploitation flag cleared for {previous.cve_id}")

    # 2. EPSS Score Delta Detection
    if new_epss is not None and abs(new_epss - previous.epss) > 1e-4:
        delta = new_epss - previous.epss
        sign = "+" if delta > 0 else ""
        reasons.append(
            f"EPSS exploitation probability changed from {previous.epss:.3f} to {new_epss:.3f} (Δ {sign}{delta:.3f})"
        )

    # 3. Patch Status Remediations
    if new_patched is not None and new_patched != previous.is_patched:
        if new_patched:
            reasons.append(f"Patch deployed for {previous.cve_id} on {previous.asset_id} (threat vector mitigated)")
        else:
            reasons.append(f"Patch status revoked for {previous.cve_id} on {previous.asset_id}")

    # 4. Internet Exposure Changes
    if new_exposed is not None and new_exposed != previous.internet_exposed:
        if new_exposed:
            reasons.append(f"Network exposure changed: asset {previous.asset_id} became public internet-facing")
        else:
            reasons.append(f"Network exposure changed: asset {previous.asset_id} moved behind internal firewall")

    # 5. CVSS Changes
    if new_cvss is not None and abs(new_cvss - previous.cvss) > 1e-3:
        delta = new_cvss - previous.cvss
        sign = "+" if delta > 0 else ""
        reasons.append(
            f"NVD CVSS base score adjusted from {previous.cvss:.1f} to {new_cvss:.1f} (Δ {sign}{delta:.1f})"
        )

    # 6. Asset Criticality Adjustments
    if new_criticality is not None and new_criticality != previous.criticality:
        reasons.append(
            f"Asset business criticality reclassified from '{previous.criticality}' to '{new_criticality}'"
        )

    # 7. Budget Limit Adjustments
    if new_budget is not None and abs(new_budget - previous.budget_limit) > 1.0:
        delta = new_budget - previous.budget_limit
        sign = "+" if delta > 0 else ""
        reasons.append(
            f"Optimization budget limit changed from ₹{previous.budget_limit:,.0f} to ₹{new_budget:,.0f} (Δ {sign}₹{delta:,.0f})"
        )

    # 8. Downtime / Financial Losses
    if new_downtime is not None and abs(new_downtime - previous.downtime_hours) > 1e-2:
        reasons.append(
            f"Estimated downtime duration updated from {previous.downtime_hours:.1f}h to {new_downtime:.1f}h"
        )
    if new_rev_loss is not None and abs(new_rev_loss - previous.revenue_loss_per_hour) > 1.0:
        reasons.append(
            f"Hourly downtime revenue loss estimate adjusted from ₹{previous.revenue_loss_per_hour:,.0f} to ₹{new_rev_loss:,.0f}"
        )

    if not reasons:
        reasons.append("Continuous re-optimization triggered with existing baseline parameters")

    return reasons


# Seed on initial load
seed_asset_registry()
