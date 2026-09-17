# TRINETRA — Monte Carlo Cyber Risk Simulation Layer

### AI-Powered Continuous Cyber Risk Quantification & Investment Optimization Platform
**SIH 2026 &middot; Theme: Blockchain & Cybersecurity &middot; Problem ID: SIH26105**
**Role:** DEV 2 (Monte Carlo Simulation Layer)

---

## 1. Overview & Purpose

The **Monte Carlo Simulation Layer** extends the deterministic Expected Annual Loss ($\text{EAL}$) produced by DEV 1's **Financial CRQ Layer** into a probabilistic risk distribution. 

In real-world cybersecurity, breach costs and incident frequencies are inherently uncertain:
- Outage duration varies depending on whether backups are corrupted.
- Forensics and legal fees depend on attacker dwell time and regulatory scrutiny.
- Attack frequency varies across threat actor campaigns.

Instead of presenting single-point estimates, the Monte Carlo simulation executes thousands of randomized trials (default: **10,000 iterations**) to generate **Value at Risk (VaR)** percentiles (**P50, P75, P90, P95, P99**) and **loss exceedance distribution histograms**.

```
┌──────────────────────────────────────────────┐
│            Cyber Risk Engine                 │
│    (CVSS, EPSS, KEV, Exposure, Crit)         │
│          → Likelihood [0-1]                  │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│         Financial CRQ Module (DEV 1)         │
│    - Baseline Frequency & Loss Components    │
│    - Expected Annual Loss (EAL)              │
│    - MonteCarloInput Handoff Payload         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│      Monte Carlo Simulation (DEV 2)          │
│    - Min / Mode / Max per Parameter          │
│    - N Iterations (100 to 100,000)           │
│    - Component-wise Triangular Distributions │
└──────────────────────┬───────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌───────────────────┐       ┌───────────────────┐
│ Percentiles (VaR) │       │  Histogram Bins   │
│ P50, P75, P90...  │       │  Frontend Charts  │
└────────┬──────────┘       └────────┬──────────┘
         │                           │
         └─────────────┬─────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│         MonteCarloResult API Output          │
│        → Executive Risk Dashboard            │
│        → Future Investment Optimizer         │
└──────────────────────────────────────────────┘
```

---

## 2. Why Monte Carlo in Cyber Risk Quantification?

1. **Captures Non-Linear Uncertainty:** Combining uncertain downtime with uncertain hourly rates produces a fat-tailed distribution that single-point multiplication cannot reveal.
2. **Quantifies Tail Risk (Catastrophic Loss):** Board members need to know not just the average loss ($\text{EAL}$), but the worst-case 1-in-100 year loss ($\text{P99}$) to determine cyber insurance limits and capital reserves.
3. **Avoids "Flaw of Averages":** An asset with moderate average loss but extreme tail exposure requires different prioritization than an asset with steady, predictable losses.

---

## 3. Why Triangular Distributions for the MVP?

For the MVP, variables are sampled using **Triangular Distributions** defined by three intuitive parameters:
- $\text{min}$: Best-case lower bound
- $\text{mode}$: Most likely estimate (derived from DEV 1's baseline)
- $\text{max}$: Worst-case upper bound

$$\text{Triangular}(\text{min}, \text{mode}, \text{max})$$

### Advantages for Cybersecurity MVP:
- **No Complex Parameter Tuning:** Does not require estimating logarithmic standard deviations ($\sigma$) or shape parameters ($\alpha, \beta$) with limited enterprise historical data.
- **Directly Elicitable:** CISOs and IT asset owners can easily answer: *"What is the minimum, typical, and maximum downtime if this database goes down?"*
- **Computationally Lightweight:** Pure Python `random.triangular()` executes 10,000 full-pipeline iterations in **$< 40\text{ms}$** without GPU or heavy framework dependencies.

---

## 4. Expected Loss vs. Percentile Metrics

| Metric | Statistical Meaning | Executive Interpretation |
|---|---|---|
| **Mean Annual Loss** | Arithmetic mean across all simulated scenarios | The long-term average loss expected per year. |
| **P50 (Median)** | 50th Percentile | In 50% of simulated years, total loss will be *below* this amount. |
| **P75** | 75th Percentile | Elevated loss threshold (1-in-4 year scenario). |
| **P90 (VaR 90%)** | 90th Percentile (Value at Risk) | 1-in-10 year loss expectation. There is only a 10% chance of exceeding this amount. |
| **P95 (VaR 95%)** | 95th Percentile | Severe cyber incident threshold (1-in-20 year scenario). |
| **P99 (VaR 99%)** | 99th Percentile | Worst-case catastrophic scenario (1-in-100 year tail risk). |

---

## 5. API Endpoints

### 1. Direct Monte Carlo Simulation
- **Method:** `POST`
- **Path:** `/monte-carlo/simulate`

#### Request Body (`MonteCarloInput`):
```json
{
  "asset_id": "AST-001",
  "cve_id": "CVE-001",
  "iterations": 10000,
  "seed": 42,
  "currency": "INR",
  "frequency_min": 0.20,
  "frequency_mode": 0.40,
  "frequency_max": 0.80,
  "downtime_hours_min": 4.0,
  "downtime_hours_mode": 8.0,
  "downtime_hours_max": 24.0,
  "revenue_loss_per_hour_min": 30000.0,
  "revenue_loss_per_hour_mode": 50000.0,
  "revenue_loss_per_hour_max": 75000.0,
  "incident_response_cost_min": 50000.0,
  "incident_response_cost_mode": 100000.0,
  "incident_response_cost_max": 180000.0,
  "recovery_cost_min": 100000.0,
  "recovery_cost_mode": 200000.0,
  "recovery_cost_max": 350000.0,
  "regulatory_legal_cost_min": 20000.0,
  "regulatory_legal_cost_mode": 50000.0,
  "regulatory_legal_cost_max": 120000.0,
  "customer_business_impact_min": 30000.0,
  "customer_business_impact_mode": 75000.0,
  "customer_business_impact_max": 150000.0
}
```

#### Response Body (`MonteCarloResult`):
```json
{
  "asset_id": "AST-001",
  "cve_id": "CVE-001",
  "iterations": 10000,
  "mean_annual_loss": 481105.78,
  "p50": 444652.79,
  "p75": 603215.12,
  "p90": 789432.65,
  "p95": 925184.34,
  "p99": 1234509.81,
  "min_loss": 74520.15,
  "max_loss": 1845210.42,
  "currency": "INR",
  "model_version": "MC-MVP-1.0",
  "distribution": "triangular",
  "simulation_assumptions": {
    "frequency_distribution": "triangular",
    "loss_distribution": "component-wise triangular",
    "iterations": 10000,
    "seed": 42,
    "model_type": "stochastic"
  },
  "histogram": [
    {
      "lower_bound": 74520.15,
      "upper_bound": 192566.17,
      "count": 680,
      "percentage": 6.8
    }
  ],
  "explanation": [
    "Executed 10,000 Monte Carlo stochastic iterations using component-wise triangular probability distributions.",
    "Mean Expected Annual Loss: ₹481,105.78 across simulated scenarios.",
    "Median Annual Loss (P50): ₹444,652.79 (50% probability annual loss is below this threshold).",
    "75th Percentile Exposure (P75): ₹603,215.12.",
    "90th Percentile Value at Risk (P90): ₹789,432.65 (1-in-10 year loss expectation).",
    "95th Percentile Severe Risk (P95): ₹925,184.34 (1-in-20 year loss expectation).",
    "99th Percentile Worst-Case Tail Exposure (P99): ₹1,234,509.81 (1-in-100 year catastrophic loss scenario).",
    "Observed simulated loss range: ₹74,520.15 to ₹1,845,210.42."
  ]
}
```

---

### 2. Convenience Bridge Endpoint: Simulate from Financial CRQ
- **Method:** `POST`
- **Path:** `/monte-carlo/from-crq`
- **Description:** Takes DEV 1's `FinancialCRQInput` and applies spread multipliers (`frequency_spread_min`, `frequency_spread_max`, `cost_spread_min`, `cost_spread_max`) to execute simulation without re-specifying individual min/max bounds.

---

### 3. Module Health Check
- **Method:** `GET`
- **Path:** `/monte-carlo/health`
- **Response:**
```json
{
  "status": "ok",
  "module": "monte-carlo",
  "model_version": "MC-MVP-1.0"
}
```

---

## 6. Future Investment Optimizer Integration Guide

The future **Security Investment Optimization Engine** will consume `MonteCarloResult` metrics:
1. **Risk Reduction Objective:** Measure security control impact by evaluating $\Delta \text{EAL}$ and $\Delta \text{P90}$ across simulated portfolios.
2. **Constraint-Based Optimization:** Given a budget $B$, solve:
   $$\max \sum_{i} \Delta \text{EAL}_i \quad \text{subject to} \quad \sum c_i \le B$$
3. **Tail Risk Mitigation:** Prioritize controls that reduce P99 catastrophic loss for mission-critical assets.
