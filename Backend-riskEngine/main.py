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
from risk.constants import MODEL_VERSION

app = FastAPI(
    title="TRINETRA Cyber Risk Engine",
    description="""
### AI-Powered Continuous Cyber Risk Quantification & Investment Optimization Platform
**SIH 2026 &middot; Deterministic Cyber Risk Scoring Engine**

This backend module performs deterministic, explainable risk scoring by synthesizing:
- Technical severity (**CVSS**)
- Real-world weaponization & exploit probability (**EPSS**)
- Active exploitation intelligence (**CISA KEV**)
- Operational exposure (**Internet Facing**)
- Business context (**Asset Criticality**)

Provides complete mathematical breakdowns and rule-based risk drivers for explainability.
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

# Mount the Risk Engine router
app.include_router(risk_router)


@app.get("/", tags=["General"])
def root_info():
    """Root metadata endpoint with pointers to documentation and health check."""
    return {
        "project": "TRINETRA - Cyber Risk Quantification & Investment Optimization",
        "module": "Risk Engine",
        "version": "1.0.0",
        "model_version": MODEL_VERSION,
        "swagger_docs": "/docs",
        "redoc_docs": "/redoc",
        "health_check": "/risk/health",
    }


if __name__ == "__main__":
    import uvicorn

    print(f"Starting TRINETRA Risk Engine (Model: {MODEL_VERSION})...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
