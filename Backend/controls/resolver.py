"""Control Dependency Resolver for Cybersecurity Investment Optimization

TRINETRA - AI-Powered Continuous Cyber Risk Quantification Platform
SIH 2026 - Problem ID: SIH26105

Coordinates recursive dependency resolution, cycle detection, asset applicability,
single-count implementation costing, and budget constraint validation.
"""

import copy
import logging
from typing import Dict, List, Optional, Set, Tuple

from .catalog import get_all_controls, get_control_by_id
from .models import (
    ControlDependencyResolution,
    DependencyItem,
    SecurityControl,
)

logger = logging.getLogger("trinetra.controls.resolver")


class CircularDependencyError(ValueError):
    """Raised when a circular control dependency chain is detected."""
    pass


def is_control_applicable(
    control: SecurityControl,
    target_asset_type: str,
    allow_override: bool = False,
) -> Tuple[bool, Optional[str]]:
    """Validate whether a security control is architecturally applicable to an asset archetype."""
    if allow_override:
        return True, None

    target_norm = (target_asset_type or "all").strip().lower()
    applicable_norm = [t.strip().lower() for t in control.applicable_asset_types]

    if "all" in applicable_norm or target_norm in applicable_norm:
        return True, None

    return (
        False,
        f"Control '{control.control_id}' is not designated for asset type '{target_asset_type}' "
        f"(Applicable types: {', '.join(control.applicable_asset_types)})",
    )


class ControlDependencyResolver:
    """Validates, bundles, and resolves security control dependencies recursively."""

    def __init__(
        self,
        controls_pool: Optional[List[SecurityControl]] = None,
        asset_type: str = "web_application",
        budget_limit: float = 1800000.0,
        existing_controls: Optional[List[str]] = None,
        allow_override: bool = False,
        candidate_ids: Optional[Set[str]] = None,
    ):
        if budget_limit < 0:
            raise ValueError("Budget limit must be non-negative.")

        self.asset_type = asset_type or "web_application"
        self.budget_limit = float(budget_limit)
        self.allow_override = allow_override
        self.existing_controls: Set[str] = set(
            c.strip().upper() for c in (existing_controls or []) if c
        )
        self.candidate_ids: Optional[Set[str]] = (
            set(c.strip().upper() for c in candidate_ids if c)
            if candidate_ids is not None
            else None
        )

        # Build fast lookup map from pool or default catalog
        self.catalog_map: Dict[str, SecurityControl] = {}
        for c in get_all_controls():
            self.catalog_map[c.control_id.strip().upper()] = c


        if controls_pool:
            for c in controls_pool:
                self.catalog_map[c.control_id.strip().upper()] = c

    def get_control(self, control_id: str) -> Optional[SecurityControl]:
        """Lookup control in the active catalog pool."""
        return self.catalog_map.get(control_id.strip().upper())

    def detect_cycles(self, root_ids: List[str]) -> None:
        """Perform DFS cycle detection across control dependencies.
        
        Raises CircularDependencyError("Circular control dependency detected.") if a cycle exists.
        """
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def _dfs(cid: str, path: List[str]) -> None:
            norm_id = cid.strip().upper()
            if norm_id in visiting:
                cycle_str = " -> ".join(path + [norm_id])
                raise CircularDependencyError(
                    f"Circular control dependency detected: {cycle_str}"
                )
            if norm_id in visited:
                return

            visiting.add(norm_id)
            ctrl = self.catalog_map.get(norm_id)
            if ctrl and ctrl.required_dependencies:
                for dep in ctrl.required_dependencies:
                    _dfs(dep, path + [norm_id])

            visiting.remove(norm_id)
            visited.add(norm_id)

        for root in root_ids:
            norm_root = root.strip().upper()
            if norm_root not in visited:
                _dfs(norm_root, [])

    def resolve_bundle(
        self,
        control: SecurityControl,
        already_selected_ids: Set[str],
        remaining_budget: float,
    ) -> ControlDependencyResolution:
        """Resolve all recursive prerequisite dependencies for a single candidate control."""
        cid = control.control_id.strip().upper()

        # 1. Check cycle starting at this control
        self.detect_cycles([cid])

        # 2. Check applicability of the primary control
        app_ok, app_reason = is_control_applicable(
            control, self.asset_type, self.allow_override
        )
        if not app_ok:
            return ControlDependencyResolution(
                control_id=control.control_id,
                status="rejected",
                dependencies=[],
                bundle_cost=control.implementation_cost,
                bundle_annual_cost=control.annual_cost,
                rejection_reason=app_reason or f"Control '{control.control_id}' is not applicable to asset",
            )

        # 3. Recursively collect all dependencies in topological dependency order
        ordered_deps: List[str] = []
        dep_visited: Set[str] = set()
        dep_errors: List[DependencyItem] = []

        def _collect_deps(curr_id: str) -> None:
            curr_ctrl = self.catalog_map.get(curr_id)
            if not curr_ctrl or not curr_ctrl.required_dependencies:
                return

            for dep_id in curr_ctrl.required_dependencies:
                norm_dep = dep_id.strip().upper()
                if norm_dep in dep_visited:
                    continue
                dep_visited.add(norm_dep)

                # Check if dependency is within candidate pool if candidate_ids restriction is active
                if (
                    self.candidate_ids is not None
                    and norm_dep not in self.candidate_ids
                    and norm_dep not in self.existing_controls
                    and norm_dep not in already_selected_ids
                ):
                    dep_errors.append(
                        DependencyItem(
                            control_id=dep_id,
                            status="unavailable",
                            reason=f"Dependency constraint: Prerequisite control '{dep_id}' is not in candidates or existing controls",
                        )
                    )
                    continue

                dep_ctrl = self.catalog_map.get(norm_dep)
                if not dep_ctrl:
                    dep_errors.append(
                        DependencyItem(
                            control_id=dep_id,
                            status="unavailable",
                            reason=f"Required dependency control '{dep_id}' does not exist in catalog",
                        )
                    )
                    continue


                # Check dependency applicability to asset
                dep_app_ok, dep_app_reason = is_control_applicable(
                    dep_ctrl, self.asset_type, self.allow_override
                )
                if not dep_app_ok:
                    dep_errors.append(
                        DependencyItem(
                            control_id=dep_ctrl.control_id,
                            status="unavailable",
                            reason="Dependency is not applicable or exceeds budget",
                        )
                    )
                    continue

                # Recurse into nested dependencies first
                _collect_deps(norm_dep)
                ordered_deps.append(norm_dep)

        _collect_deps(cid)

        # If any required dependency is missing or inapplicable, reject control
        if dep_errors:
            total_est_cost = control.implementation_cost + sum(
                self.catalog_map[d].implementation_cost
                for d in ordered_deps
                if d in self.catalog_map
            )
            return ControlDependencyResolution(
                control_id=control.control_id,
                status="rejected",
                dependencies=dep_errors,
                bundle_cost=total_est_cost,
                bundle_annual_cost=control.annual_cost,
                rejection_reason="Required dependency cannot be satisfied",
            )

        # 4. Determine which dependencies need to be newly included and calculate single bundle cost
        newly_needed_deps: List[SecurityControl] = []
        dep_items: List[DependencyItem] = []

        for d_id in ordered_deps:
            dep_obj = self.catalog_map[d_id]
            if d_id in already_selected_ids or d_id in self.existing_controls:
                dep_items.append(
                    DependencyItem(
                        control_id=dep_obj.control_id,
                        status="included",
                        reason="Already satisfied by existing enterprise controls",
                    )
                )
            else:
                newly_needed_deps.append(dep_obj)
                dep_items.append(
                    DependencyItem(
                        control_id=dep_obj.control_id,
                        status="included",
                        reason="Required dependency",
                    )
                )

        # Implementation cost counted exactly once
        additional_dep_cost = sum(d.implementation_cost for d in newly_needed_deps)
        additional_annual_cost = sum(d.annual_cost for d in newly_needed_deps)
        primary_cost = control.implementation_cost if cid not in already_selected_ids else 0.0

        bundle_cost = primary_cost + additional_dep_cost
        bundle_annual_cost = control.annual_cost + additional_annual_cost

        # 5. Validate bundle cost against remaining budget
        if bundle_cost > remaining_budget:
            # Mark newly needed dependencies as unavailable due to budget
            unavailable_deps: List[DependencyItem] = []
            for item in dep_items:
                if any(d.control_id == item.control_id for d in newly_needed_deps):
                    unavailable_deps.append(
                        DependencyItem(
                            control_id=item.control_id,
                            status="unavailable",
                            reason="Dependency is not applicable or exceeds budget",
                        )
                    )
                else:
                    unavailable_deps.append(item)

            rejection_msg = (
                "Required dependency cannot be satisfied"
                if newly_needed_deps
                else f"Implementation cost (₹{bundle_cost:,.0f}) exceeds available budget (₹{remaining_budget:,.0f})"
            )

            return ControlDependencyResolution(
                control_id=control.control_id,
                status="rejected",
                dependencies=unavailable_deps,
                bundle_cost=bundle_cost,
                bundle_annual_cost=bundle_annual_cost,
                rejection_reason=rejection_msg,
            )

        # 6. Success: bundle is accepted
        return ControlDependencyResolution(
            control_id=control.control_id,
            status="selected",
            dependencies=dep_items,
            bundle_cost=bundle_cost,
            bundle_annual_cost=bundle_annual_cost,
            rejection_reason=None,
        )

    def resolve_all(
        self,
        requested_controls: List[SecurityControl],
    ) -> List[ControlDependencyResolution]:
        """Resolve and bundle all requested controls in sequential/priority order."""
        if self.budget_limit < 0:
            raise ValueError("Budget limit must be non-negative.")

        # Deduplicate requested controls while preserving order
        seen_cids: Set[str] = set()
        unique_requested: List[SecurityControl] = []
        for ctrl in requested_controls:
            norm_id = ctrl.control_id.strip().upper()
            if norm_id not in seen_cids:
                seen_cids.add(norm_id)
                unique_requested.append(ctrl)

        # Global cycle check before resolving
        all_ids = [c.control_id for c in unique_requested]
        self.detect_cycles(all_ids)

        selected_ids: Set[str] = set(self.existing_controls)
        remaining_budget = self.budget_limit
        resolutions: List[ControlDependencyResolution] = []

        for ctrl in unique_requested:
            res = self.resolve_bundle(
                control=ctrl,
                already_selected_ids=selected_ids,
                remaining_budget=remaining_budget,
            )
            resolutions.append(res)

            if res.status == "selected":
                selected_ids.add(ctrl.control_id.strip().upper())
                for dep_item in res.dependencies:
                    if dep_item.status == "included":
                        selected_ids.add(dep_item.control_id.strip().upper())
                remaining_budget = max(0.0, remaining_budget - res.bundle_cost)

        return resolutions
