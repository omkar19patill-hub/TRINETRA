"""TRINETRA Cyber Risk Input Service - Main Application Entrypoint

Smart India Hackathon (SIH) 2026
Theme: Blockchain & Cybersecurity | Problem ID: SIH26105
Platform: AI-Powered Continuous Cyber Risk Quantification and Investment Optimization

Person 1: FastAPI Application for Risk Input Ingestion and Validation.
"""

import sys
from pathlib import Path

# Ensure Backend-input directory is in python module search path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from risk.routes import router as risk_router

app = FastAPI(
    title="TRINETRA Cyber Risk Input Service",
    description="""
### AI-Powered Continuous Cyber Risk Quantification & Investment Optimization Platform
**SIH 2026 &middot; Cyber Risk Input Ingestion & Validation Module**

This service handles clean, validated input ingestion for the TRINETRA Cyber Risk Engine:
- **CVSS base score validation** [0.0 - 10.0]
- **EPSS exploitation probability validation** [0.0 - 1.0]
- **CISA KEV catalog threat signal validation** (boolean)
- **Asset internet exposure status** (boolean)
- **Asset business criticality verification** ('Critical', 'High', 'Medium', 'Low')
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend integration and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the Risk router: POST /risk/calculate
app.include_router(risk_router)


@app.get("/", tags=["General"])
def root_info():
    """Root metadata endpoint with pointers to documentation and health check."""
    return {
        "project": "TRINETRA - Cyber Risk Quantification & Investment Optimization",
        "module": "Risk Input & Validation Service",
        "version": "1.0.0",
        "swagger_docs": "/docs",
        "redoc_docs": "/redoc",
        "risk_calculate_endpoint": "/risk/calculate",
    }


if __name__ == "__main__":
    import uvicorn

    print("Starting TRINETRA Risk Input Service on http://0.0.0.0:8000 ...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
