# TRINETRA — Unified Cyber Risk Quantification & Threat Intelligence Engine

### AI-Powered Continuous Cyber Risk Quantification and Investment Optimization Platform
**SIH 2026 &middot; Theme: Blockchain & Cybersecurity &middot; Problem ID: SIH26105**

---

## 1. Overview & Request Pipeline

`Backend-riskEngine` is the **primary backend application** for the TRINETRA cybersecurity platform. It unifies real-time threat intelligence ingestion, validation, normalization, and caching with deterministic risk quantification, financial cyber-risk modeling (Open FAIR), and stochastic Monte Carlo simulation into a single unified service.

### Unified Request Pipeline

```
┌────────────────────────────────────────────────────────┐
│ Data Upload / Live Official Threat Feeds (NVD, EPSS,   │
│               CISA KEV, MITRE ATT&CK)                  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│   Ingestion Layer (Mode A Live Sync / Mode B Bulk)     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│     Validation (CVE format, CVSS [0-10], EPSS [0-1])   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Normalization (UnifiedVulnerabilityRecord & Provenance)│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Multi-Tier Cache (In-Memory LRU + SQLite WAL Storage)  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Asset Join (/vulnerabilities/risk-engine-payload)      │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Deterministic Risk Engine (/risk/calculate)            │
│  - Likelihood: 25% CVSS + 40% EPSS + 20% KEV + 15% Exp │
│  - Impact Multiplier: [0.25 - 1.00] from Criticality   │
│  - Risk Score: [0.0 - 100.0] & Explainable Drivers     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Financial CRQ Engine (/financial-crq/calculate)        │
│  - Downtime Loss = Revenue Loss/hr × Downtime Hours    │
│  - Total Loss Magnitude = Downtime + Response + Legal  │
│  - Event Frequency = Baseline Freq × Likelihood        │
│  - Expected Annual Loss (EAL) = Frequency × Magnitude  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Monte Carlo Simulation (/monte-carlo/simulate)         │
│  - 1,000 - 100,000 Stochastic Iterations               │
│  - Triangular / PERT Distribution Sampling             │
│  - Percentiles (P50, P75, P90, P95, P99) & Histograms  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```text
Backend-riskEngine/
├── main.py               # Primary FastAPI unified entrypoint (Port 8000)
├── config.py             # Centralized configuration & environment settings
├── requirements.txt      # Dependency specification
│
├── api/                  # Unified API Layer
│   ├── __init__.py       # Router exports
│   ├── risk.py           # /risk endpoints
│   └── ingestion.py      # /vulnerabilities & /ingestion endpoints
│
├── risk/                 # Deterministic Cyber Risk Scoring
│   ├── constants.py      # Factor weights (CVSS:0.25, EPSS:0.40, KEV:0.20, EXP:0.15)
│   ├── schemas.py        # RiskCalculationRequest & RiskCalculationResponse
│   ├── scoring.py        # Likelihood, Impact, Risk Score, and Risk Level
│   ├── drivers.py        # Explainable qualitative risk driver generator
│   ├── engine.py         # Decoupled risk calculation orchestrator
│   └── tests.py          # Legacy unit test suite
│
├── financial_crq/        # Financial Cyber Risk Quantification (Open FAIR)
│   ├── schemas.py        # FinancialCRQInput, FinancialCRQResult, MonteCarloInput
│   ├── engine.py         # Downtime loss, total loss magnitude, EAL, explanation
│   ├── routes.py         # /financial-crq routes
│   └── tests.py          # Legacy financial CRQ test suite
│
├── monte_carlo/          # Stochastic Uncertainty Simulation
│   ├── schemas.py        # MonteCarloInput, MonteCarloResult, HistogramBin
│   ├── simulator.py      # Monte Carlo sampler, percentiles, histogram builder
│   ├── routes.py         # /monte-carlo routes
│   └── tests.py          # Legacy Monte Carlo test suite
│
├── schemas/              # Threat Intelligence Schemas
│   ├── __init__.py       # Schemas package init
│   └── vulnerability.py  # UnifiedVulnerabilityRecord, EnrichedVulnerabilityResponse, etc.
│
├── validation/           # Data Validation Layer
│   ├── __init__.py       # Validation package init
│   └── vulnerability_validator.py  # Strict regex, bounds checking [0-10, 0-1]
│
├── normalization/        # Data Normalization Layer
│   ├── __init__.py       # Normalization package init
│   └── vulnerability_normalizer.py # Normalization to canonical schema
│
├── integrations/         # Official Threat Intelligence Adapters
│   ├── __init__.py       # Adapters package init
│   ├── nvd.py            # NVD 2.0 API client with backoff & rate-limiting
│   ├── epss.py           # FIRST EPSS API client with batch queries
│   ├── cisa_kev.py       # CISA KEV JSON catalog client with O(1) in-memory index
│   └── mitre_attack.py   # MITRE ATT&CK contextual mapping
│
├── cache/                # Multi-Tier Storage & Caching
│   ├── __init__.py       # Cache package init
│   └── vulnerability_cache.py # SQLite persistent store (WAL mode) + LRU memory cache
│
├── ingestion/            # Ingestion Service & Workers
│   ├── __init__.py       # Ingestion package init
│   ├── service.py        # Central IngestionService with recalculation hooks
│   ├── scheduler.py      # Periodic bulk synchronization scheduler
│   └── status.py         # Telemetry & observability metrics tracker
│
└── tests/                # Comprehensive Automated Test Suite (95 tests)
    ├── test_unified_backend.py     # App initialization, metadata, health checks
    ├── test_end_to_end.py          # Full pipeline E2E test
    ├── test_risk_engine.py         # Risk scoring benchmarks & boundaries
    ├── test_financial_crq.py       # Financial loss & EAL calculations
    ├── test_monte_carlo.py         # Monte Carlo simulation & percentiles
    ├── test_api_routes.py          # Ingestion & vulnerability endpoints
    ├── test_cache_storage.py       # SQLite persistence & filtering
    ├── test_cisa_kev.py            # CISA KEV indexing & lookups
    ├── test_epss.py                # FIRST EPSS single & batch lookups
    ├── test_nvd.py                 # NVD 2.0 CVSS parsing & resiliency
    ├── test_mitre_attack.py        # ATT&CK enrichment heuristics
    ├── test_normalization.py       # Normalization & contract transforms
    └── test_validation.py          # Input boundary & format validation
```

---

## 3. Configuration & Environment Variables

Configuration is loaded from environment variables or a local `.env` file via [config.py](file:///d:/TRINETRA/Backend-riskEngine/config.py).

| Environment Variable | Default Value | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Primary server bind address |
| `PORT` | `8000` | Primary server listening port |
| `DEBUG` | `false` | Enable debug logging |
| `DATABASE_PATH` | `./vulnerabilities.db` | Path to local SQLite storage file |
| `CACHE_MAX_ENTRIES` | `5000` | Maximum records in memory LRU cache |
| `CACHE_TTL_SECONDS` | `86400` (24h) | In-memory cache TTL |
| `ENABLE_SCHEDULER` | `true` | Enable background bulk synchronization worker |
| `SYNC_INTERVAL_HOURS` | `6.0` | Interval between scheduled bulk synchronizations |
| `NVD_API_KEY` | `None` | Optional NVD 2.0 API key (increases rate limit) |
| `NVD_BASE_URL` | `https://services.nvd.nist.gov/rest/json/cves/2.0` | Official NVD endpoint |
| `EPSS_BASE_URL` | `https://api.first.org/data/v1/epss` | Official FIRST EPSS endpoint |
| `CISA_KEV_FEED_URL` | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | CISA KEV JSON catalog feed |

---

## 4. Starting the Primary Backend Application

### 1. Install Dependencies
```bash
cd Backend-riskEngine
pip install -r requirements.txt
```

### 2. Start Server
```bash
uvicorn main:app --reload --port 8000
```
Or directly:
```bash
python main.py
```

- **Interactive Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Root Metadata & Discovery:** [http://localhost:8000/](http://localhost:8000/)

---

## 5. API Endpoint Catalog

### General & Metadata
- `GET /` — Root metadata endpoint advertising all modules, active model versions, and registered API routes.

### Threat Intelligence & Ingestion
- `GET /vulnerabilities/{cve_id}/enriched` — Retrieve normalized threat intelligence (CVSS, EPSS, KEV) from cache.
- `POST /vulnerabilities/risk-engine-payload` — Combine asset context with CVE intelligence into Risk Engine payload.
- `POST /ingestion/vulnerability/{cve_id}/refresh` — Trigger live upstream sync for a single CVE across official sources.
- `POST /ingestion/bulk-sync` — Trigger on-demand bulk sync for CISA KEV catalog and watchlist CVEs.
- `GET /ingestion/health` — Probe live reachability for NVD, EPSS, CISA KEV, and local database.
- `GET /ingestion/status` — Operational telemetry, sync timestamps, record counts, and cache metrics.
- `GET /vulnerabilities` — Paginated querying and filtering of cached vulnerability catalog.

### Deterministic Risk Engine
- `POST /risk/calculate` — Calculate deterministic risk score, likelihood, impact multiplier, and explainable risk drivers.
- `GET /risk/health` — Risk Engine module health check.

### Financial CRQ (Open FAIR)
- `POST /financial-crq/calculate` — Compute Downtime Loss, Total Loss Magnitude, Annual Event Frequency, and EAL.
- `GET /financial-crq/health` — Financial CRQ module health check.

### Stochastic Monte Carlo Simulation
- `POST /monte-carlo/simulate` — Run 1,000–100,000 iterations stochastic simulation with PERT/Triangular sampling.
- `POST /monte-carlo/from-crq` — Bridge Financial CRQ output directly into Monte Carlo simulation.
- `GET /monte-carlo/health` — Monte Carlo module health check.

---

## 6. Running Tests

### Complete Unified Test Suite (95 tests)
```bash
cd Backend-riskEngine
python -m pytest tests -v
```

### Legacy Subpackage Test Verification
```bash
cd Backend-riskEngine
python -m pytest risk/tests.py financial_crq/tests.py monte_carlo/tests.py -v
```
