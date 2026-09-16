"""API package for the TRINETRA platform."""
from .risk import router as risk_router

__all__ = ["risk_router"]
