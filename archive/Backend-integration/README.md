# TRINETRA — Real-Time Cybersecurity Threat Intelligence Integration Layer

### AI-Powered Continuous Cyber Risk Quantification and Investment Optimization Platform
**SIH 2026 &middot; Theme: Blockchain & Cybersecurity &middot; Problem ID: SIH26105**

---

## 1. Overview & Objectives

The **Cybersecurity Data Integration Layer** is the real-time threat intelligence backbone of the TRINETRA platform. It autonomously collects, validates, normalizes, deduplicates, and caches official vulnerability intelligence from:

1. **National Vulnerability Database (NVD 2.0 API)**: Technical CVSS metrics (v3.1, v4.0, v2.0), vector strings, severity tiers, descriptions, and affected CPE configurations.
2. **FIRST EPSS API**: Real-world exploit prediction probability $[0.0 - 1.0]$ and percentile ranks from live weaponization telemetry.
3. **CISA Known Exploited Vulnerabilities (KEV) Catalog**: Authoritative CISA feed for confirmed in-the-wild exploitation, ransomware campaign associations, and binding remediation due dates.
4. **MITRE ATT&CK**: Decoupled threat context enrichment mapping tactics, techniques, software, and adversary group profiles.

### Architecture Data Flow

```text
  ┌────────────────────────────────────────────────────────┐
  │              OFFICIAL EXTERNAL THREAT FEEDS            │
  │     NVD 2.0 API    │   FIRST EPSS API   │   CISA KEV   │
  └─────────┬──────────┴─────────┬──────────┴──────┬───────┘
            │                    │                 │
            ▼                    ▼                 ▼
  ┌────────────────────────────────────────────────────────┐
  │                 API Source Adapters                    │
  │  - Exponential Backoff & Random Jitter                 │
  │  - 429 Rate-Limit Throttling & 5xx Recovery            │
  │  - Optional NVD API Key in Request Headers             │
  │  - Graceful Degradation / Stale Fallback               │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │                   Validation Layer                     │
  │  - Strict CVE Regex Format: ^CVE-\d{4}-\d{4,7}$        │
  │  - Numeric Range Guards: CVSS [0, 10], EPSS [0, 1]     │
  │  - ISO 8601 Timestamps & Type Sanitization             │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │                 Normalization Layer                    │
  │  - UnifiedVulnerabilityRecord Schema                   │
  │  - Strict Source Provenance: NVD, FIRST, CISA          │
  │  - Data Freshness & Raw Payloads for Auditing          │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │             Storage & Two-Tier Cache                   │
  │  - Tier 1: In-Memory LRU Cache (Sub-ms Retrieval)      │
  │  - Tier 2: Persistent SQLite DB with WAL Mode          │
  │  - Atomic Upsert on cve_id (Zero Duplication)          │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │               REST API & Event Hooks                   │
  │  - GET  /vulnerabilities/{id}/enriched                 │
  │  - POST /vulnerabilities/risk-engine-payload           │
  │  - POST /ingestion/vulnerability/{id}/refresh          │
  │  - GET  /ingestion/health (Active Network Probes)      │
  │  - GET  /ingestion/status (Telemetry Metrics)          │
  │  - Re-calculation Event Dispatcher                     │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
               TRINETRA Risk Engine (Backend-riskEngine)
```

---

## 2. Directory Structure

```text
Backend-integration/
├── integrations/
│   ├── __init__.py
│   ├── nvd.py               # NVD 2.0 API client (retry, jitter, 429 handling, API key header)
│   ├── epss.py              # FIRST EPSS API client (rate limiting, batch & single lookup)
│   ├── cisa_kev.py          # CISA KEV JSON catalog loader & O(1) in-memory index
│   └── mitre_attack.py      # MITRE ATT&CK enrichment adapter
│
├── validation/
│   ├── __init__.py
│   └── vulnerability_validator.py  # Regex, boundary guards, and audit rejection logger
│
├── normalization/
│   ├── __init__.py
│   └── vulnerability_normalizer.py # UnifiedVulnerabilityRecord builder & provenance mapper
│
├── cache/
│   ├── __init__.py
│   └── vulnerability_cache.py      # Memory LRU + SQLite persistent database with atomic upsert
│
├── ingestion/
│   ├── __init__.py
│   ├── service.py           # Ingestion orchestrator & recalculation hook dispatcher
│   ├── scheduler.py         # Mode B background bulk sync worker
│   └── status.py            # Telemetry counters, sync times, and uptime tracker
│
├── schemas/
│   ├── __init__.py
│   └── vulnerability.py     # Pydantic v2 schemas for all API contracts
│
├── api/
│   ├── __init__.py
│   └── ingestion.py         # FastAPI REST endpoints
│
├── tests/
│   ├── test_nvd.py
│   ├── test_epss.py
│   ├── test_cisa_kev.py
│   ├── test_mitre_attack.py
│   ├── test_validation.py
│   ├── test_normalization.py
│   ├── test_cache_storage.py
│   ├── test_ingestion_service.py
│   ├── test_api_routes.py
│   └── test_end_to_end.py
│
├── config.py                # Environment configuration loader
├── main.py                  # FastAPI entrypoint with CORS & startup seeders
├── requirements.txt         # Dependencies
├── .env.example             # Safe environment configuration template
└── README.md                # Documentation & Postman guide
```

---

## 3. Setup & Running Locally

### Step 1: Navigate to Directory
```powershell
cd d:\TRINETRA\Backend-integration
```

### Step 2: Create & Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run Automated Tests (39 unit/integration tests with mocks)
```powershell
pytest tests -v
```

### Step 5: Start the Integration Service
```powershell
python main.py
```
*Alternatively:*
```powershell
uvicorn main:app --reload --port 8002
```

The service will be live at:
- **Root URL**: `http://localhost:8002`
- **Interactive Swagger UI**: [http://localhost:8002/docs](http://localhost:8002/docs)
- **ReDoc Documentation**: [http://localhost:8002/redoc](http://localhost:8002/redoc)

---

## 4. Postman & cURL Testing Guide

### Endpoint 1: Health Check (Active Upstream Probes)

- **Method:** `GET`
- **URL:** `http://localhost:8002/ingestion/health`

```powershell
curl -X GET "http://localhost:8002/ingestion/health"
```

#### Expected Response (`200 OK`):
```json
{
  "status": "ok",
  "module": "cybersecurity-data-integration",
  "sources": {
    "nvd": "available",
    "epss": "available",
    "cisa_kev": "available",
    "database": "available"
  },
  "checked_at": "2026-09-17T13:00:00Z"
}
```

---

### Endpoint 2: Get Enriched Intelligence for Risk Engine

- **Method:** `GET`
- **URL:** `http://localhost:8002/vulnerabilities/CVE-2026-1234/enriched`

```powershell
curl -X GET "http://localhost:8002/vulnerabilities/CVE-2026-1234/enriched"
```

#### Expected Response (`200 OK`):
```json
{
  "cve_id": "CVE-2026-1234",
  "cvss": 9.8,
  "cvss_version": "3.1",
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "epss": 0.82,
  "epss_percentile": 0.97,
  "kev": true,
  "known_ransomware_use": false,
  "severity": "CRITICAL",
  "description": "Remote Code Execution vulnerability in core web application gateway allowing unauthenticated root access.",
  "source_metadata": {
    "cvss_source": "NVD",
    "epss_source": "FIRST",
    "kev_source": "CISA",
    "sources": ["NVD", "EPSS", "CISA_KEV", "MITRE_ATTACK"],
    "source_statuses": {}
  },
  "data_freshness": {
    "nvd_last_modified": "2026-01-20T14:30:00Z",
    "epss_date": "2026-02-01",
    "kev_checked_at": "2026-09-17T13:00:00Z",
    "source_updated_at": "2026-01-20T14:30:00Z",
    "ingested_at": "2026-09-17T13:00:00Z"
  }
}
```

---

### Endpoint 3: Asset Join -> Risk Engine Payload Constructor

- **Method:** `POST`
- **URL:** `http://localhost:8002/vulnerabilities/risk-engine-payload`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "asset_id": "AST-001",
  "cve_id": "CVE-2026-1234",
  "internet_exposed": true,
  "criticality": "Critical"
}
```

```powershell
curl -X POST "http://localhost:8002/vulnerabilities/risk-engine-payload" `
  -H "Content-Type: application/json" `
  -d '{"asset_id": "AST-001", "cve_id": "CVE-2026-1234", "internet_exposed": true, "criticality": "Critical"}'
```

#### Expected Response (`200 OK` — Matches `Backend-riskEngine` Input Contract):
```json
{
  "asset_id": "AST-001",
  "cve_id": "CVE-2026-1234",
  "cvss": 9.8,
  "epss": 0.82,
  "kev": true,
  "internet_exposed": true,
  "criticality": "Critical",
  "metadata": {
    "cvss_source": "NVD",
    "epss_source": "FIRST",
    "kev_source": "CISA",
    "data_freshness": {
      "nvd_last_modified": "2026-01-20T14:30:00Z",
      "epss_date": "2026-02-01",
      "kev_checked_at": "2026-09-17T13:00:00Z",
      "source_updated_at": "2026-01-20T14:30:00Z",
      "ingested_at": "2026-09-17T13:00:00Z"
    }
  }
}
```

---

### Endpoint 4: Force Live Synchronization for a Single CVE (Mode A)

- **Method:** `POST`
- **URL:** `http://localhost:8002/ingestion/vulnerability/CVE-2024-3400/refresh`

```powershell
curl -X POST "http://localhost:8002/ingestion/vulnerability/CVE-2024-3400/refresh"
```

#### Expected Response (`200 OK` — Complete Unified Record):
```json
{
  "cve_id": "CVE-2024-3400",
  "nvd": {
    "cvss": 10.0,
    "cvss_version": "3.1",
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
    "severity": "CRITICAL",
    "published": "2024-04-12T17:15:49.000",
    "last_modified": "2024-04-18T18:15:08.000",
    "description": "A command injection vulnerability in Palo Alto Networks PAN-OS...",
    "affected_products": ["cpe:2.3:o:paloaltonetworks:pan-os:10.2.0:*:*:*:*:*:*:*"]
  },
  "epss": {
    "score": 0.93874,
    "percentile": 0.9912,
    "date": "2026-03-01"
  },
  "kev": {
    "is_known_exploited": true,
    "date_added": "2024-04-12",
    "known_ransomware_use": true,
    "required_action": "Apply mitigations per vendor instructions or discontinue use.",
    "due_date": "2024-04-19"
  },
  "mitre_attack": {
    "tactics": ["Initial Access", "Execution", "Impact"],
    "techniques": ["T1190 - Exploit Public-Facing Application", "T1486 - Data Encrypted for Impact"],
    "groups": ["Lazarus Group", "LockBit"],
    "software": ["Cobalt Strike", "LockBit 3.0"],
    "status": "available"
  },
  "data_freshness": {
    "nvd_last_modified": "2024-04-18T18:15:08.000",
    "epss_date": "2026-03-01",
    "kev_checked_at": "2026-09-17T13:00:00Z",
    "source_updated_at": "2024-04-18T18:15:08.000",
    "ingested_at": "2026-09-17T13:00:00Z"
  },
  "metadata": {
    "cvss_source": "NVD",
    "epss_source": "FIRST",
    "kev_source": "CISA",
    "sources": ["NVD", "EPSS", "CISA_KEV", "MITRE_ATTACK"],
    "source_statuses": {
      "nvd": "available",
      "epss": "available",
      "cisa_kev": "available"
    }
  }
}
```

---

### Endpoint 5: Telemetry & Observability Status

- **Method:** `GET`
- **URL:** `http://localhost:8002/ingestion/status`

```powershell
curl -X GET "http://localhost:8002/ingestion/status"
```

#### Expected Response (`200 OK`):
```json
{
  "status": "ok",
  "last_sync": {
    "nvd": "2026-09-17T13:00:00Z",
    "epss": "2026-09-17T13:00:00Z",
    "cisa_kev": "2026-09-17T13:00:00Z",
    "bulk_sync": "2026-09-17T13:00:00Z"
  },
  "records": {
    "processed": 12,
    "updated": 4,
    "failed": 0
  },
  "cache_stats": {
    "db_total_count": 12,
    "in_memory_count": 12,
    "cisa_kev_matched_count": 5
  },
  "uptime_seconds": 184.5
}
```

---

### Endpoint 6: Query Stored Vulnerabilities

- **Method:** `GET`
- **URL:** `http://localhost:8002/vulnerabilities?page=1&page_size=10&kev_only=true`

```powershell
curl -X GET "http://localhost:8002/vulnerabilities?page=1&page_size=10&kev_only=true"
```

---

## 5. Integrating with TRINETRA Risk Engine

The Integration Layer and Risk Engine work together seamlessly without coupling:

```python
import httpx

# 1. Fetch normalized threat intelligence + asset context from Integration Layer
integration_url = "http://localhost:8002/vulnerabilities/risk-engine-payload"
asset_request = {
    "asset_id": "AST-001",
    "cve_id": "CVE-2024-3400",
    "internet_exposed": True,
    "criticality": "Critical",
}
payload_resp = httpx.post(integration_url, json=asset_request)
risk_engine_payload = payload_resp.json()

# 2. Forward payload directly to TRINETRA Risk Engine
risk_engine_url = "http://localhost:8000/risk/calculate"
risk_resp = httpx.post(risk_engine_url, json=risk_engine_payload)
final_risk_quantification = risk_resp.json()

print(f"Computed Risk Score: {final_risk_quantification['risk_score']} ({final_risk_quantification['risk_level']})")
```
