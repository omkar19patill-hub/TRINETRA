# TRINETRA — Cyber Risk Engine Module

### AI-Powered Continuous Cyber Risk Quantification and Investment Optimization Platform
**SIH 2026 &middot; Theme: Blockchain & Cybersecurity &middot; Problem ID: SIH26105**

---

## 1. Overview

The **Risk Engine** is the deterministic, explainable cyber risk scoring module of the TRINETRA platform. It takes vulnerability severity metrics (CVSS, EPSS, CISA KEV) paired with asset operational context (Internet exposure, business criticality) and computes:

1. **Likelihood of Exploitation** $[0.0 - 1.0]$
2. **Business Impact Multiplier** $[0.0 - 1.0]$
3. **Overall Risk Score** $[0.0 - 100.0]$
4. **Categorical Risk Level** (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
5. **Explainable Risk Drivers** (Human-readable justifications for why the score is high)
6. **Detailed Calculation Breakdown** (Individual factor contributions for auditing)
7. **Model Governance Metadata** (`risk-model-v1`, deterministic)

### Decoupled Layered Architecture

```
                 API REQUEST
                     ↓
              Pydantic Schema (Validation)
                     ↓
                Risk Engine (Orchestrator)
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
    Likelihood     Impact      Drivers
        ↓            ↓            ↓
        └────────────┼────────────┘
                     ↓
               Risk Result
                     ↓
                API Response
```

The core scoring logic (`risk/engine.py`, `risk/scoring.py`, `risk/drivers.py`) is completely independent of FastAPI and HTTP. It can be invoked directly by batch ingestion scripts, database workers, or background queues.

---

## 2. Directory Structure

```text
Backend-riskEngine/
│
├── risk/
│   ├── __init__.py       # Package exports
│   ├── constants.py      # Weights, impact mappings, thresholds, model metadata
│   ├── schemas.py        # Pydantic request & response schemas + validation
│   ├── scoring.py        # Mathematical scoring functions (Likelihood, Impact, Risk Score, Level)
│   ├── drivers.py        # Explainable rule-based risk driver generator
│   ├── engine.py         # Core orchestrator decoupled from HTTP
│   └── tests.py          # 19 automated unit & integration tests
│
├── api/
│   ├── __init__.py       # Router exports
│   └── risk.py           # FastAPI routes: POST /risk/calculate, GET /risk/health
│
├── main.py               # FastAPI application entrypoint with CORS & Swagger UI
├── requirements.txt      # Dependency specification
└── README.md             # Documentation & Postman testing guide
```

---

## 3. Mathematical Model & Formulas

### Step 1: CVSS Normalization

$$\text{CVSS}_{\text{normalized}} = \frac{\text{CVSS}}{10.0}$$

- CVSS $10.0 \rightarrow 1.0$
- CVSS $5.0 \rightarrow 0.5$
- CVSS $0.0 \rightarrow 0.0$

### Step 2: Exploitation Likelihood

$$\text{Likelihood} = (0.25 \times \text{CVSS}_{\text{normalized}}) + (0.40 \times \text{EPSS}) + (0.20 \times \text{KEV}_{\text{signal}}) + (0.15 \times \text{Exposure}_{\text{signal}})$$

Where binary signals are:
- $\text{KEV}_{\text{signal}} = 1$ if listed in CISA KEV catalog, else $0$
- $\text{Exposure}_{\text{signal}} = 1$ if asset is internet-facing, else $0$

Configurable constants in `risk/constants.py`:
```python
CVSS_WEIGHT = 0.25
EPSS_WEIGHT = 0.40
KEV_WEIGHT = 0.20
EXPOSURE_WEIGHT = 0.15
```

### Step 3: Business Impact

Deterministic mapping from asset business criticality:
```python
CRITICALITY_IMPACT = {
    "Critical": 1.00,
    "High":     0.75,
    "Medium":   0.50,
    "Low":      0.25,
}
```

### Step 4: Overall Risk Score

$$\text{Risk Score} = \text{Likelihood} \times \text{Impact} \times 100$$

- Clamped strictly within $[0.0, 100.0]$
- Rounded to 2 decimal places

### Step 5: Categorical Risk Level

| Score Range | Risk Level |
|---|---|
| $75.0 - 100.0$ | **CRITICAL** |
| $50.0 - 74.99$ | **HIGH** |
| $25.0 - 49.99$ | **MEDIUM** |
| $0.0 - 24.99$ | **LOW** |

### Step 6: Explainable Risk Drivers

Rule-based conditions trigger explainability tags:
- $\text{CVSS} \ge 9.0 \implies$ `"Critical CVSS"`
- $\text{EPSS} \ge 0.70 \implies$ `"High exploitation probability"`
- $\text{KEV} == \text{True} \implies$ `"Known exploited vulnerability"`
- $\text{internet\_exposed} == \text{True} \implies$ `"Internet exposed asset"`
- $\text{criticality} == \text{"Critical"} \implies$ `"Critical business asset"`

---

## 4. Setup & Running Locally

### Prerequisites
- Python 3.11+ (Python 3.13 recommended)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Automated Unit Tests
```bash
pytest risk/tests.py -v
```

### 3. Start the FastAPI Server
```bash
uvicorn main:app --reload --port 8000
```
Or directly:
```bash
python main.py
```

The server will be live at: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`

---

## 5. Postman Testing Guide

### Endpoint 1: Health Check

- **Method:** `GET`
- **URL:** `http://localhost:8000/risk/health`
- **Headers:** None needed

#### Expected Response (`200 OK`):
```json
{
  "status": "ok",
  "module": "risk-engine",
  "model_version": "risk-model-v1"
}
```

---

### Endpoint 2: Calculate Risk (Benchmark Scenario 1 — Critical Risk)

- **Method:** `POST`
- **URL:** `http://localhost:8000/risk/calculate`
- **Headers:**
  - `Content-Type: application/json`
- **Request Body (raw JSON):**
```json
{
  "asset_id": "AST-001",
  "cve_id": "CVE-2026-1234",
  "cvss": 9.8,
  "epss": 0.82,
  "kev": true,
  "internet_exposed": true,
  "criticality": "Critical"
}
```

#### Expected Response (`200 OK`):
```json
{
  "asset_id": "AST-001",
  "cve_id": "CVE-2026-1234",
  "likelihood": 0.923,
  "impact": 1.0,
  "risk_score": 92.3,
  "risk_level": "CRITICAL",
  "risk_drivers": [
    "Critical CVSS",
    "High exploitation probability",
    "Known exploited vulnerability",
    "Internet exposed asset",
    "Critical business asset"
  ],
  "calculation": {
    "cvss_normalized": 0.98,
    "epss": 0.82,
    "kev_signal": 1,
    "exposure_signal": 1,
    "cvss_contribution": 0.245,
    "epss_contribution": 0.328,
    "kev_contribution": 0.2,
    "exposure_contribution": 0.15
  },
  "model": {
    "version": "risk-model-v1",
    "type": "deterministic"
  }
}
```

---

### Endpoint 3: Calculate Risk (Technical Severity vs. Low Business Impact)

Demonstrates how technical severity ($0.955$ likelihood) is dampened by low business criticality ($0.25$).

- **Method:** `POST`
- **URL:** `http://localhost:8000/risk/calculate`
- **Headers:**
  - `Content-Type: application/json`
- **Request Body (raw JSON):**
```json
{
  "asset_id": "AST-DEV-009",
  "cve_id": "CVE-2026-9999",
  "cvss": 9.8,
  "epss": 0.90,
  "kev": true,
  "internet_exposed": true,
  "criticality": "Low"
}
```

#### Expected Response (`200 OK`):
```json
{
  "asset_id": "AST-DEV-009",
  "cve_id": "CVE-2026-9999",
  "likelihood": 0.955,
  "impact": 0.25,
  "risk_score": 23.88,
  "risk_level": "LOW",
  "risk_drivers": [
    "Critical CVSS",
    "High exploitation probability",
    "Known exploited vulnerability",
    "Internet exposed asset"
  ],
  "calculation": {
    "cvss_normalized": 0.98,
    "epss": 0.9,
    "kev_signal": 1,
    "exposure_signal": 1,
    "cvss_contribution": 0.245,
    "epss_contribution": 0.36,
    "kev_contribution": 0.2,
    "exposure_contribution": 0.15
  },
  "model": {
    "version": "risk-model-v1",
    "type": "deterministic"
  }
}
```

---

### Endpoint 4: Validation Error Handling

Testing rejection of invalid inputs (e.g., CVSS out of bounds or invalid criticality).

- **Method:** `POST`
- **URL:** `http://localhost:8000/risk/calculate`
- **Headers:**
  - `Content-Type: application/json`
- **Request Body (raw JSON):**
```json
{
  "asset_id": "AST-001",
  "cve_id": "CVE-2026-1234",
  "cvss": 14.5,
  "epss": 1.25,
  "kev": true,
  "internet_exposed": true,
  "criticality": "SuperUrgent"
}
```

#### Expected Response (`422 Unprocessable Entity`):
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "cvss"],
      "msg": "Input should be less than or equal to 10"
    },
    {
      "type": "less_than_equal",
      "loc": ["body", "epss"],
      "msg": "Input should be less than or equal to 1"
    },
    {
      "type": "enum",
      "loc": ["body", "criticality"],
      "msg": "Input should be 'Critical', 'High', 'Medium' or 'Low'"
    }
  ]
}
```

---

## 6. Assumptions & Extensibility

### Prototype Assumptions
1. **Weight Distribution:** The weights ($0.25, 0.40, 0.20, 0.15$) represent prototype heuristic assumptions for the SIH 2026 hackathon. EPSS is weighted highest ($0.40$) to reflect real-world exploitation probability over theoretical vulnerability severity.
2. **Impact Scale:** Business criticality maps linearly from $0.25$ (Low) to $1.00$ (Critical) to demonstrate asset-aware prioritization.

### Future Extension Points
1. **Open FAIR Integration:** The Likelihood output directly maps to Threat Event Frequency (TEF) / Vulnerability (V), and Impact can be multiplied by Expected Financial Loss ($\text{EAL} = \text{Loss Event Frequency} \times \text{Loss Magnitude}$).
2. **Monte Carlo Simulation:** Replace fixed scalar impact with lognormal loss magnitude distributions.
3. **Control Effectiveness:** Introduce mitigating security control factors (e.g. WAF, EDR presence) to discount Likelihood or Impact.
4. **Dynamic Driver Rules:** In `risk/drivers.py`, additional `DriverRule` evaluators can be added (e.g., ransomware group affiliation, lateral movement hops).
