"""TRINETRA Security Controls Catalog Module

SIH 2026 - Problem ID: SIH26105
"""

CONTROLS_MODEL_VERSION = "CTRL-1.0"

from .catalog import get_all_controls, get_control_by_id, get_controls_by_ids
from .models import (
    ControlAssessmentItem,
    ControlAssessRequest,
    ControlAssessResponse,
    ControlCatalogResponse,
    ControlDependencyResolution,
    ControlDependencyResolveRequest,
    DependencyItem,
    RiskReductionEffect,
    SecurityControl,
)
from .resolver import CircularDependencyError, ControlDependencyResolver, is_control_applicable
from .routes import router

__all__ = [
    "CONTROLS_MODEL_VERSION",
    "SecurityControl",
    "RiskReductionEffect",
    "ControlAssessmentItem",
    "ControlAssessRequest",
    "ControlAssessResponse",
    "ControlCatalogResponse",
    "ControlDependencyResolution",
    "ControlDependencyResolveRequest",
    "DependencyItem",
    "CircularDependencyError",
    "ControlDependencyResolver",
    "is_control_applicable",
    "get_all_controls",
    "get_control_by_id",
    "get_controls_by_ids",
    "router",
]

