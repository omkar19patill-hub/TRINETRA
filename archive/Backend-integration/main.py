"""TRINETRA Cybersecurity Data Integration Layer - Application Entrypoint

Smart India Hackathon (SIH) 2026
Theme: Blockchain & Cybersecurity | Problem ID: SIH26105
Platform: AI-Powered Continuous Cyber Risk Quantification & Investment Optimization
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure directory is in Python module search path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ingestion import router as ingestion_router, set_ingestion_service
from config import settings
from ingestion.scheduler import IngestionScheduler
from ingestion.service import IngestionService
from schemas.vulnerability import (
    DataFreshness,
    EPSSNormalized,
    KEVNormalized,
    NVDNormalized,
    RawMitreAttackData,
    SourceMetadata,
    UnifiedVulnerabilityRecord,
)

# Configure logging format
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("trinetra.main")

# Global singleton service and scheduler
service_instance = IngestionService()
scheduler_instance = IngestionScheduler(service=service_instance)
set_ingestion_service(service_instance)


def seed_benchmark_vulnerabilities(service: IngestionService):
    """Seed key benchmark CVEs into local storage for immediate offline availability & testing."""
    sample_records = [
        UnifiedVulnerabilityRecord(
            cve_id="CVE-2026-1234",
            nvd=NVDNormalized(
                cvss=9.8,
                cvss_version="3.1",
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                severity="CRITICAL",
                published="2026-01-15T10:00:00Z",
                last_modified="2026-01-20T14:30:00Z",
                description="Remote Code Execution vulnerability in core web application gateway allowing unauthenticated root access.",
                affected_products=["cpe:2.3:a:enterprise:gateway:1.0:*:*:*:*:*:*:*"],
            ),
            epss=EPSSNormalized(
                score=0.82,
                percentile=0.97,
                date="2026-02-01",
            ),
            kev=KEVNormalized(
                is_known_exploited=True,
                date_added="2026-01-22",
                known_ransomware_use=False,
                required_action="Apply vendor mitigation patches immediately.",
                due_date="2026-02-12",
            ),
            mitre_attack=RawMitreAttackData(
                tactics=["Initial Access", "Execution"],
                techniques=["T1190 - Exploit Public-Facing Application"],
                groups=["Lazarus Group", "APT29"],
                software=["Cobalt Strike"],
            ),
            data_freshness=DataFreshness(
                nvd_last_modified="2026-01-20T14:30:00Z",
                epss_date="2026-02-01",
                kev_checked_at="2026-09-17T13:00:00Z",
                source_updated_at="2026-01-20T14:30:00Z",
                ingested_at="2026-09-17T13:00:00Z",
            ),
            metadata=SourceMetadata(
                cvss_source="NVD",
                epss_source="FIRST",
                kev_source="CISA",
                sources=["NVD", "EPSS", "CISA_KEV", "MITRE_ATTACK"],
            ),
        ),
        UnifiedVulnerabilityRecord(
            cve_id="CVE-2021-44228",
            nvd=NVDNormalized(
                cvss=10.0,
                cvss_version="3.1",
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                severity="CRITICAL",
                published="2021-12-10T10:15:00Z",
                last_modified="2023-11-07T03:39:00Z",
                description="Apache Log4j2 JNDI features used in configuration, log messages, and parameters do not protect against attacker controlled LDAP and other JNDI related endpoints.",
                affected_products=["cpe:2.3:a:apache:log4j:2.0:*:*:*:*:*:*:*"],
            ),
            epss=EPSSNormalized(
                score=0.975,
                percentile=0.999,
                date="2026-03-01",
            ),
            kev=KEVNormalized(
                is_known_exploited=True,
                date_added="2021-12-10",
                known_ransomware_use=True,
                required_action="Apply updates per vendor instructions.",
                due_date="2021-12-24",
            ),
            data_freshness=DataFreshness(
                nvd_last_modified="2023-11-07T03:39:00Z",
                epss_date="2026-03-01",
                kev_checked_at="2026-09-17T13:00:00Z",
                source_updated_at="2023-11-07T03:39:00Z",
                ingested_at="2026-09-17T13:00:00Z",
            ),
            metadata=SourceMetadata(
                cvss_source="NVD",
                epss_source="FIRST",
                kev_source="CISA",
                sources=["NVD", "EPSS", "CISA_KEV"],
            ),
        ),
    ]

    for record in sample_records:
        service.storage.upsert_vulnerability(record)
    logger.info("[Main] Seeded %d benchmark vulnerabilities into local cache.", len(sample_records))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event management."""
    logger.info("[Main] Initializing TRINETRA Cybersecurity Data Integration Layer...")
    seed_benchmark_vulnerabilities(service_instance)

    # Start background scheduler
    scheduler_instance.start()

    yield

    logger.info("[Main] Shutting down Integration Layer...")
    scheduler_instance.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
### AI-Powered Continuous Cyber Risk Quantification & Investment Optimization Platform
**SIH 2026 &middot; Real-Time Cybersecurity Threat Intelligence Integration Layer**

This layer ingests, validates, normalizes, and caches real-time threat intelligence from official sources:
- **NVD 2.0 API** (CVSS v3.1/v4.0/v2.0 base scores, vector strings, severity, descriptions)
- **FIRST EPSS API** (Exploit Prediction Scoring System exploitation probabilities)
- **CISA KEV Catalog** (Authoritative Known Exploited Vulnerabilities feed & ransomware campaign tracking)
- **MITRE ATT&CK** (Optional threat context enrichment: tactics, techniques, software, adversary groups)

Provides high-performance cached internal contracts for the **TRINETRA Risk Engine**.
""",
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount router
app.include_router(ingestion_router)


@app.get("/", tags=["General"])
def root_metadata():
    """Root endpoint providing service metadata and API discovery links."""
    return {
        "project": "TRINETRA - Cyber Risk Quantification & Investment Optimization",
        "module": "Cybersecurity Threat Intelligence Data Integration Layer",
        "version": settings.PROJECT_VERSION,
        "swagger_docs": "/docs",
        "redoc_docs": "/redoc",
        "endpoints": {
            "enriched_vulnerability": "/vulnerabilities/{cve_id}/enriched",
            "asset_join_risk_payload": "/vulnerabilities/risk-engine-payload",
            "single_cve_refresh": "/ingestion/vulnerability/{cve_id}/refresh",
            "health_check": "/ingestion/health",
            "telemetry_status": "/ingestion/status",
            "list_vulnerabilities": "/vulnerabilities",
        },
    }


if __name__ == "__main__":
    import uvicorn

    print(f"Starting {settings.PROJECT_NAME} on http://{settings.HOST}:{settings.PORT} ...")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
