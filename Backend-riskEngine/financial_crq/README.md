# TRINETRA — Financial Cyber Risk Quantification (CRQ) Layer

### AI-Powered Continuous Cyber Risk Quantification & Investment Optimization Platform
**SIH 2026 &middot; Theme: Blockchain & Cybersecurity &middot; Problem ID: SIH26105**
**Role:** DEV 1 (Financial CRQ Layer)

---

## 1. Overview & Purpose

The **Financial Cyber Risk Quantification (CRQ) Layer** converts technical and operational cyber risk scores into an explainable, modeled financial representation. 

While technical metrics (CVSS, EPSS, CISA KEV) determine vulnerability severity and threat likelihood, executive boards and CISOs require actionable financial metrics:
- *What is our modeled Expected Annual Loss ($\text{EAL}$)?*
- *What is the financial loss magnitude if a breach occurs on this asset?*
- *How much downtime revenue, incident recovery cost, and regulatory liability are at risk?*

This module bridges the gap between the upstream **Cyber Risk Engine** and the downstream **Monte Carlo Simulation Engine (DEV 2)**.

```
┌─────────────────────────────────────────┐
│            Cyber Risk Engine            │
│  (CVSS, EPSS, KEV, Exposure, Crit)     │
│   → Likelihood [0-1], Score [0-100]     │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│           Financial CRQ Input           │
│   - Asset context & Likelihood score    │
│   - Revenue rate & Downtime hours       │
│   - IR, Recovery, Legal, SLA impacts    │
└────────────────────┬────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   Loss Event    │     │      Loss       │
│    Frequency    │     │    Magnitude    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
┌─────────────────────────────────────────┐
│       Expected Annual Loss (EAL)        │
│    = Event Frequency × Loss Magnitude   │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│     CRQ Output & MonteCarloInput        │
│          (Handoff to DEV 2)             │
└─────────────────────────────────────────┘
```

---

## 2. Distinction: Cyber Risk Score vs. Financial Cyber Risk

| Dimension | Cyber Risk Engine (`/risk`) | Financial CRQ Layer (`/financial-crq`) |
|---|---|---|
| **Primary Metric** | Dimensionless composite score $[0.0 - 100.0]$ | Monetary loss ($\text{EAL}$ in ₹ INR / USD) |
| **Inputs** | Technical telemetry (CVSS, EPSS, KEV, internet exposure, asset criticality) | Operational downtime, hourly revenue rates, forensics, IT restoration, legal fines, customer SLA costs |
| **Likelihood vs Frequency** | Exploitation likelihood index $[0.0 - 1.0]$ | Modeled Annual Loss Event Frequency (events/year) |
| **Audience** | Security engineers & SOC analysts | CISO, CFO, Board of Directors, Cyber Insurers |

> [!IMPORTANT]
> **Model Score vs. Real-World Probability:**
> The cyber risk score and likelihood $[0.0 - 1.0]$ are **model-derived scores**, not guaranteed empirical probabilities of attack. The Financial CRQ layer uses an explicit, configurable modeling assumption ($\text{baseline\_annual\_frequency}$) to convert this score into a modeled event frequency.

---

## 3. Mathematical Model & Formulas

### Step 1: Direct Downtime Loss
$$\text{Downtime Loss} = \text{revenue\_loss\_per\_hour} \times \text{downtime\_hours}$$

*Example:*
$$\text{Downtime Loss} = ₹50,000/\text{hr} \times 8\text{ hrs} = ₹400,000$$

---

### Step 2: Total Loss Magnitude
Total financial damage incurred during a single security breach event:
$$\text{Total Loss Magnitude} = \text{Downtime Loss} + \text{IR Cost} + \text{Recovery Cost} + \text{Legal/Regulatory Cost} + \text{Customer Impact}$$

*Example:*
$$\begin{aligned}
\text{Total Loss Magnitude} &= ₹400,000 \text{ (downtime)} \\
&+ ₹100,000 \text{ (incident response)} \\
&+ ₹200,000 \text{ (recovery)} \\
&+ ₹50,000 \text{ (regulatory/legal)} \\
&+ ₹75,000 \text{ (customer impact)} \\
&= \mathbf{₹825,000}
\end{aligned}$$

---

### Step 3: Modeled Loss Event Frequency
$$\text{Annual Event Frequency} = \text{baseline\_annual\_frequency} \times \text{likelihood}$$

*Example:*
$$\text{Annual Event Frequency} = 1.00 \text{ event/yr} \times 0.40 = \mathbf{0.40 \text{ events/year}}$$

- **Configurable Baseline:** `baseline_annual_frequency` defaults to `1.0` event/year for prototype demonstration.
- **Production Calibration:** In production deployment, this baseline is calibrated against historical organizational incident logs or industry-specific telemetry.

---

### Step 4: Expected Annual Loss (EAL)
$$\text{Expected Annual Loss (EAL)} = \text{Annual Event Frequency} \times \text{Total Loss Magnitude}$$

*Example:*
$$\text{EAL} = 0.40 \text{ events/yr} \times ₹825,000 = \mathbf{₹330,000/\text{year}}$$

> [!NOTE]
> $\text{EAL}$ is a modeled mathematical expectation under stated assumptions, not a guaranteed prediction or forecast.

---

## 4. API Endpoints

### 1. Calculate Financial CRQ
- **Method:** `POST`
- **Path:** `/financial-crq/calculate`
- **Status:** `200 OK`

#### Example Request:
```json
{
  "asset_id": "AST-001",
  "cve_id": "CVE-001",
  "likelihood": 0.40,
  "risk_score": 60.0,
  "criticality": "High",
  "revenue_loss_per_hour": 50000.0,
  "downtime_hours": 8.0,
  "incident_response_cost": 100000.0,
  "recovery_cost": 200000.0,
  "regulatory_legal_cost": 50000.0,
  "customer_business_impact": 75000.0,
  "baseline_annual_frequency": 1.0,
  "currency": "INR"
}
```

#### Example Response:
```json
{
  "asset_id": "AST-001",
  "cve_id": "CVE-001",
  "likelihood": 0.4,
  "baseline_annual_frequency": 1.0,
  "annual_event_frequency": 0.4,
  "downtime_loss": 400000.0,
  "incident_response_cost": 100000.0,
  "recovery_cost": 200000.0,
  "regulatory_legal_cost": 50000.0,
  "customer_business_impact": 75000.0,
  "total_loss_magnitude": 825000.0,
  "expected_annual_loss": 330000.0,
  "currency": "INR",
  "assumptions": [
    "Baseline annual frequency (1.00 events/yr) is a configurable prototype modeling assumption.",
    "Likelihood (0.4000) is derived from technical CVSS/EPSS/KEV indicators and represents a model score, not an empirical attack probability.",
    "Financial cost parameters and downtime durations are organization-provided estimates or synthetic demonstration values.",
    "Expected Annual Loss (EAL = ₹330,000.00) represents a modeled statistical expectation under current assumptions, not a guaranteed loss forecast."
  ],
  "model_version": "CRQ-MVP-1.0",
  "explanation": [
    "Modeled event frequency: 0.40 events/year (Likelihood: 0.40 × Baseline frequency: 1.00 events/yr)",
    "Downtime loss: ₹400,000.00 (8.00 hrs × ₹50,000.00/hr)",
    "Incident response & forensics cost: ₹100,000.00",
    "System recovery & data reconstruction cost: ₹200,000.00",
    "Regulatory penalties & legal defense cost: ₹50,000.00",
    "Customer compensation & SLA penalty impact: ₹75,000.00",
    "Total modeled loss per event (Loss Magnitude): ₹825,000.00",
    "Expected Annual Loss (EAL): ₹330,000.00 (0.40 events/yr × ₹825,000.00/event)"
  ],
  "monte_carlo_input": {
    "asset_id": "AST-001",
    "cve_id": "CVE-001",
    "annual_frequency_assumption": 0.4,
    "downtime_hours": 8.0,
    "revenue_loss_per_hour": 50000.0,
    "incident_response_cost": 100000.0,
    "recovery_cost": 200000.0,
    "regulatory_legal_cost": 50000.0,
    "customer_business_impact": 75000.0,
    "loss_magnitude": 825000.0,
    "baseline_annual_frequency": 1.0,
    "likelihood": 0.4,
    "currency": "INR"
  }
}
```

---

### 2. Financial CRQ Health Check
- **Method:** `GET`
- **Path:** `/financial-crq/health`
- **Response:**
```json
{
  "status": "ok",
  "module": "financial-crq",
  "model_version": "CRQ-MVP-1.0"
}
```

---

## 5. DEV 2 Integration & Handoff Contract (`MonteCarloInput`)

DEV 2 is responsible for implementing the probabilistic **Monte Carlo Simulation Engine**. 

The `FinancialCRQResult` provides an explicit `monte_carlo_input` payload designed specifically for DEV 2:

```python
class MonteCarloInput(BaseModel):
    asset_id: str
    cve_id: Optional[str]
    annual_frequency_assumption: float  # Baseline event rate λ for Poisson distribution
    downtime_hours: float               # Central tendency for downtime distribution
    revenue_loss_per_hour: float        # Hourly rate
    incident_response_cost: float       # Baseline cost for PERT / Triangular distribution
    recovery_cost: float                # Baseline cost for PERT / Triangular distribution
    regulatory_legal_cost: float        # Baseline cost for Lognormal distribution
    customer_business_impact: float     # Baseline cost for distribution
    loss_magnitude: float               # Central scalar loss magnitude
    baseline_annual_frequency: float
    likelihood: float
    currency: str
```

### How DEV 2 Consumes This Output:
1. **Event Frequency Simulation:** DEV 2 uses `annual_frequency_assumption` as the Poisson rate parameter $\lambda$ to simulate the number of annual breach events ($k \sim \text{Poisson}(\lambda)$).
2. **Loss Magnitude Simulation:** DEV 2 parameterizes probability distributions around each baseline component:
   - Downtime hours: $\text{PERT}(\text{min}=0.5 \times H, \text{mode}=H, \text{max}=2.5 \times H)$
   - Financial costs: $\text{Lognormal}(\mu, \sigma)$ or $\text{Triangular}(\text{low}, \text{mode}, \text{high})$
3. **Simulated Annual Loss:** Sum simulated loss magnitudes across all simulated events per trial to generate the Value at Risk (VaR) and Loss Exceedance Curves (LEC).

---

## 6. Assumptions & Governance Declarations

1. **Configurable Baseline Frequency:** `baseline_annual_frequency` is configurable on request (default: `1.0`).
2. **Synthetic Demonstration Data:** All monetary amounts (revenue loss/hour, forensics, recovery, legal fees, customer compensation) and outage durations are organization-provided estimates or synthetic demonstration values.
3. **Deterministic Explainability:** All generated explanations are purely rule-based and deterministic — no non-deterministic LLM is involved in calculating or explaining numerical financial outputs.
