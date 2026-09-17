"""TRINETRA Cyber Risk Engine - Main Application Entrypoint

Smart India Hackathon (SIH) 2026
Theme: Blockchain & Cybersecurity | Problem ID: SIH26105
Platform: AI-Powered Continuous Cyber Risk Quantification and Investment Optimization

This service provides the deterministic, explainable cyber risk scoring module.
"""

import sys
from pathlib import Path

# Ensure Backend-riskEngine directory is in python module search path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.risk import router as risk_router
from financial_crq.routes import router as financial_crq_router
from monte_carlo.routes import router as monte_carlo_router
from risk.constants import MODEL_VERSION as RISK_MODEL_VERSION
from financial_crq.engine import FINANCIAL_MODEL_VERSION
from monte_carlo.simulator import MONTE_CARLO_MODEL_VERSION

app = FastAPI(
    title="TRINETRA Cyber Risk, Financial CRQ & Monte Carlo Engine",
    description="""
### AI-Powered Continuous Cyber Risk Quantification & Investment Optimization Platform
**SIH 2026 &middot; Cyber Risk Scoring, Financial CRQ & Monte Carlo Simulation Engine**

This backend service provides:
1. **Cyber Risk Scoring Module (`/risk`):** Deterministic risk quantification synthesizing CVSS, EPSS, CISA KEV, internet exposure, and asset criticality.
2. **Financial CRQ Module (`/financial-crq`):** Financial cyber-risk modeling computing Downtime Loss, Total Loss Magnitude, Modeled Loss Event Frequency, and Expected Annual Loss (EAL).
3. **Monte Carlo Simulation Module (`/monte-carlo`):** Stochastic simulation modeling uncertainty in event frequency and loss magnitudes, providing percentiles (P50, P75, P90, P95, P99) and histogram distribution analytics.
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for future frontend integration and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(risk_router)
app.include_router(financial_crq_router)
app.include_router(monte_carlo_router)


@app.get("/", tags=["General"])
def root_info():
    """Root metadata endpoint with pointers to documentation and health checks."""
    return {
        "project": "TRINETRA - Cyber Risk Quantification & Investment Optimization",
        "modules": ["Risk Engine", "Financial CRQ", "Monte Carlo Simulation"],
        "version": "1.0.0",
        "risk_model_version": RISK_MODEL_VERSION,
        "financial_crq_model_version": FINANCIAL_MODEL_VERSION,
        "monte_carlo_model_version": MONTE_CARLO_MODEL_VERSION,
        "swagger_docs": "/docs",
        "redoc_docs": "/redoc",
        "endpoints": {
            "risk_calculate": "/risk/calculate",
            "risk_health": "/risk/health",
            "financial_crq_calculate": "/financial-crq/calculate",
            "financial_crq_health": "/financial-crq/health",
            "monte_carlo_simulate": "/monte-carlo/simulate",
            "monte_carlo_from_crq": "/monte-carlo/from-crq",
            "monte_carlo_health": "/monte-carlo/health",
        },
    }




if __name__ == "__main__":
    import uvicorn

    print(f"Starting TRINETRA Risk Engine (Model: {MODEL_VERSION})...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
