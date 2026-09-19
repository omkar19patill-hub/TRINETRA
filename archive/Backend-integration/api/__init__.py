"""TRINETRA Cybersecurity Data Integration Layer - API Package"""

from .ingestion import router as ingestion_router

__all__ = ["ingestion_router"]
