"""TRINETRA Cyber Risk & Intelligence Engine - Unified Configuration

Loads settings from environment variables or .env file with safe defaults.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Base directory for the primary backend application
BASE_DIR = Path(__file__).resolve().parent

# Load .env file if present
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Settings:
    """Application settings and API client configuration."""

    # Project metadata
    PROJECT_NAME: str = "TRINETRA Cyber Risk Quantification & Intelligence Engine"
    PROJECT_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # Official API Endpoints
    # NVD 2.0 API: https://nvd.nist.gov/developers/vulnerabilities
    NVD_BASE_URL: str = os.getenv(
        "NVD_BASE_URL", "https://services.nvd.nist.gov/rest/json/cves/2.0"
    )
    NVD_API_KEY: Optional[str] = os.getenv("NVD_API_KEY", None)

    # FIRST EPSS API: https://www.first.org/epss/api
    EPSS_BASE_URL: str = os.getenv(
        "EPSS_BASE_URL", "https://api.first.org/data/v1/epss"
    )

    # CISA KEV JSON Feed: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
    CISA_KEV_FEED_URL: str = os.getenv(
        "CISA_KEV_FEED_URL",
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    )

    # HTTP Client / Resiliency Settings
    REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10.0"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_BASE: float = float(os.getenv("RETRY_BACKOFF_BASE", "1.5"))
    RETRY_BACKOFF_MAX: float = float(os.getenv("RETRY_BACKOFF_MAX", "10.0"))

    # Rate Limiting (Requests Per Minute)
    NVD_RATE_LIMIT_RPM: int = int(
        os.getenv("NVD_RATE_LIMIT_RPM", "50" if os.getenv("NVD_API_KEY") else "10")
    )
    EPSS_RATE_LIMIT_RPM: int = int(os.getenv("EPSS_RATE_LIMIT_RPM", "600"))

    # Database & Storage
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH", str(BASE_DIR / "vulnerabilities.db")
    )

    # In-memory Cache Settings
    CACHE_MAX_ENTRIES: int = int(os.getenv("CACHE_MAX_ENTRIES", "5000"))
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24 hours

    # Bulk Synchronization Scheduler
    ENABLE_SCHEDULER: bool = os.getenv("ENABLE_SCHEDULER", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    SYNC_INTERVAL_HOURS: float = float(os.getenv("SYNC_INTERVAL_HOURS", "6.0"))

    # Downstream Risk Engine Integration URL (optional internal endpoint)
    RISK_ENGINE_BASE_URL: str = os.getenv(
        "RISK_ENGINE_BASE_URL", "http://localhost:8000"
    )


settings = Settings()
