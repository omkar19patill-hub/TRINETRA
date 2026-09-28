"""TRINETRA Cyber Risk & Intelligence Engine - Primary Backend Entrypoint

Smart India Hackathon (SIH) 2026
Theme: Blockchain & Cybersecurity | Problem ID: SIH26105
Platform: AI-Powered Continuous Cyber Risk Quantification & Investment Optimization

This primary service integrates:
1. Cyber Threat Intelligence Ingestion & Normalization Layer (NVD, EPSS, CISA KEV, MITRE ATT&CK)
2. Deterministic Cyber Risk Scoring Engine (/risk)
3. Financial Cyber Risk Quantification via Open FAIR (/financial-crq)
4. Stochastic Monte Carlo Simulation Engine (/monte-carlo)
5. Real-Time Vulnerability Intelligence & Asset Join APIs (/vulnerabilities, /ingestion)
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure Backend-riskEngine directory is in python module search path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ingestion import (
    get_ingestion_service,
    router as ingestion_router,
    set_ingestion_service,
)
from api.risk import router as risk_router
from config import settings
from financial_crq.engine import FINANCIAL_MODEL_VERSION
from financial_crq.routes import router as financial_crq_router
from ingestion.scheduler import IngestionScheduler
from ingestion.service import IngestionService
from monte_carlo.routes import router as monte_carlo_router
from monte_carlo.simulator import MONTE_CARLO_MODEL_VERSION
from decision import DECISION_MODEL_VERSION
from decision.routes import router as decision_router
from ml import ML_MODEL_VERSION
from ml.routes import router as ml_router
from ai import AI_EXPLAIN_VERSION
from ai.routes import router as ai_router
from blockchain import BLOCKCHAIN_MODEL_VERSION
from blockchain.routes import router as blockchain_router
from orchestration import ORCHESTRATION_MODEL_VERSION
from orchestration.routes import router as orchestration_router
from controls import CONTROLS_MODEL_VERSION, router as controls_router
from optimization import OPTIMIZATION_MODEL_VERSION, router as optimization_router
from risk.constants import MODEL_VERSION as RISK_MODEL_VERSION
from risk.storage import init_assessment_storage
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
    logger.info("[Main] Initializing TRINETRA Unified Cyber Risk Engine & Intelligence Layer...")
    seed_benchmark_vulnerabilities(service_instance)
    init_assessment_storage()

    # Start background scheduler if enabled
    scheduler_instance.start()

    yield

    logger.info("[Main] Shutting down TRINETRA Engine...")
    scheduler_instance.stop()


app = FastAPI(
    title="TRINETRA Cyber Risk Quantification & Intelligence Engine",
    description="""
### AI-Powered Continuous Cyber Risk Quantification & Investment Optimization Platform
**SIH 2026 &middot; Unified Backend Platform**

This primary backend service integrates:
1. **Threat Intelligence Ingestion (`/vulnerabilities`, `/ingestion`):** Live/cached NVD 2.0, FIRST EPSS, CISA KEV catalog, and MITRE ATT&CK feeds with asset join payload generation.
2. **Cyber Risk Scoring Module (`/risk`):** Deterministic risk quantification synthesizing CVSS, EPSS, CISA KEV, internet exposure, and asset criticality.
3. **Financial CRQ Module (`/financial-crq`):** Financial cyber-risk modeling computing Downtime Loss, Total Loss Magnitude, Modeled Loss Event Frequency, and Expected Annual Loss (EAL).
4. **Monte Carlo Simulation Module (`/monte-carlo`):** Stochastic simulation modeling uncertainty in event frequency and loss magnitudes, providing percentiles (P50, P75, P90, P95, P99) and histogram distribution analytics.
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for frontend integration and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(risk_router)
app.include_router(financial_crq_router)
app.include_router(monte_carlo_router)
app.include_router(decision_router)
app.include_router(controls_router)
app.include_router(optimization_router)
app.include_router(ml_router)
app.include_router(ai_router)
app.include_router(blockchain_router)
app.include_router(orchestration_router)
app.include_router(ingestion_router)


@app.get("/", tags=["General"])
def root_info():
    """Root metadata endpoint with pointers to documentation, health checks, and all modules."""
    return {
        "project": "TRINETRA - Cyber Risk Quantification & Investment Optimization",
        "modules": [
            "Threat Intelligence Ingestion",
            "Risk Engine",
            "Financial CRQ",
            "Monte Carlo Simulation",
            "Controls Catalog",
            "Investment Optimization",
            "Decision Intelligence",
            "ML Risk Calibration",
            "Explainable AI",
            "Blockchain Decision Provenance",
            "Continuous Re-Optimization",
        ],
        "version": "1.0.0",
        "risk_model_version": RISK_MODEL_VERSION,
        "financial_crq_model_version": FINANCIAL_MODEL_VERSION,
        "monte_carlo_model_version": MONTE_CARLO_MODEL_VERSION,
        "controls_model_version": CONTROLS_MODEL_VERSION,
        "optimization_model_version": OPTIMIZATION_MODEL_VERSION,
        "decision_model_version": DECISION_MODEL_VERSION,
        "ml_model_version": ML_MODEL_VERSION,
        "ai_explain_model_version": AI_EXPLAIN_VERSION,
        "blockchain_model_version": BLOCKCHAIN_MODEL_VERSION,
        "orchestration_model_version": ORCHESTRATION_MODEL_VERSION,
        "swagger_docs": "/docs",
        "redoc_docs": "/redoc",
        "endpoints": {
            "controls_list": "/controls",
            "controls_assess": "/controls/assess",
            "controls_resolve_dependencies": "/controls/resolve-dependencies",
            "optimization_run": "/optimization/run",

            "optimization_before_after": "/optimization/before-after",
            "risk_calculate": "/risk/calculate",
            "risk_assessment_batch": "/risk/assessment-batch",
            "risk_history": "/risk/history",
            "risk_latest": "/risk/latest",
            "risk_health": "/risk/health",

            "financial_crq_calculate": "/financial-crq/calculate",
            "financial_crq_health": "/financial-crq/health",
            "monte_carlo_simulate": "/monte-carlo/simulate",
            "monte_carlo_from_crq": "/monte-carlo/from-crq",
            "monte_carlo_health": "/monte-carlo/health",
            "decision_alternatives": "/decision/{optimization_id}/alternatives",
            "decision_opportunity_cost": "/decision/{optimization_id}/opportunity-cost",
            "decision_marginal_budget": "/decision/{optimization_id}/marginal-budget",
            "decision_explanation": "/decision/{optimization_id}/explanation",
            "decision_health": "/decision/health",
            "blockchain_record": "/blockchain/record",
            "blockchain_verify": "/blockchain/verify/{assessment_id}",
            "blockchain_health": "/blockchain/health",
            "blockchain_tester": "/blockchain/tester",
            "reoptimize": "/reoptimize",
            "recalculate_asset": "/recalculate/{asset_id}",
            "orchestration_health": "/orchestration/health",
            "orchestration_assets": "/orchestration/assets",
            "ml_predict": "/ml/predict",
            "ml_model_info": "/ml/model-info",
            "ml_health": "/ml/health",
            "ai_explain_risk": "/ai/explain-risk",
            "ai_explain_optimization": "/ai/explain-optimization",
            "ai_explain_scenario": "/ai/explain-scenario",
            "ai_query": "/ai/query",
            "ai_health": "/ai/health",
            "enriched_vulnerability": "/vulnerabilities/{cve_id}/enriched",
            "asset_join_risk_payload": "/vulnerabilities/risk-engine-payload",
            "single_cve_refresh": "/ingestion/vulnerability/{cve_id}/refresh",
            "bulk_sync": "/ingestion/bulk-sync",
            "ingestion_health": "/ingestion/health",
            "ingestion_status": "/ingestion/status",
            "list_vulnerabilities": "/vulnerabilities",
        },
    }


if __name__ == "__main__":
    import uvicorn

    print(
        f"Starting TRINETRA Unified Engine (Risk Model: {RISK_MODEL_VERSION}, Financial: {FINANCIAL_MODEL_VERSION}, Monte Carlo: {MONTE_CARLO_MODEL_VERSION}) on http://{settings.HOST}:{settings.PORT}..."
    )
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
