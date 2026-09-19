"""API package for the TRINETRA platform."""
from .risk import router as risk_router
from .ingestion import router as ingestion_router, set_ingestion_service, get_ingestion_service

__all__ = ["risk_router", "ingestion_router", "set_ingestion_service", "get_ingestion_service"]
