# TRINETRA Synthetic ML Training Dataset Documentation

## Dataset Metadata
- **File:** `data/ml_training.csv`
- **Purpose:** Prototype auxiliary risk-calibration and classification signal (`high_impact_event`).
- **Data Generation:** Synthetic Stochastic Generation (Monte Carlo & Rule-Augmented Cyber Heuristics).
- **Transparency Notice:** This dataset is **strictly synthetic** and generated for prototype demonstration and model calibration. It does **NOT** represent real proprietary enterprise incidents or actual breach history.

---

## 1. Feature Specifications

| Feature Name | Type | Value Range / Domain | Description |
| :--- | :--- | :--- | :--- |
| `cvss` | Float | `0.0 – 10.0` | Base Common Vulnerability Scoring System (CVSS v3.1/v4.0) score. |
| `epss` | Float | `0.0 – 1.0` | Exploit Prediction Scoring System (EPSS) probability score. |
| `kev` | Integer (0/1) | `{0, 1}` | Flag indicating if the vulnerability is listed on the CISA KEV catalog. |
| `internet_exposed` | Integer (0/1) | `{0, 1}` | Asset perimeter exposure status (1 = Internet Facing, 0 = Internal). |
| `criticality` | Categorical | `{"Critical", "High", "Medium", "Low"}` | Enterprise business criticality rating of the affected asset. |
| `asset_type` | Categorical | `{"Database", "Application Gateway", "Web Server", "API Service", "Workstation", "Cloud Storage"}` | Classification of the host asset infrastructure. |
| `business_service` | Categorical | `{"Payment Gateway", "Core Banking", "Customer Portal", "Identity Provider", "Internal Operations"}` | Enterprise service or business capability dependent on the asset. |

---

## 2. Target Variable

- **Target Column:** `high_impact_event`
- **Type:** Binary Integer (`0` or `1`)
- **Definition:**
  - `1` (**High-Impact Incident**): Represents an event scenario with high likelihood of severe operational disruption, data compromise, or significant recovery effort.
  - `0` (**Standard-Impact Incident**): Represents routine or contained vulnerability states with moderate-to-low systemic disruption.

---

## 3. Synthetic Generation Methodology & Assumptions

The synthetic training records are generated using a calibrated probabilistic generative model combining cyber threat intelligence indicators with asset operational context:

1. **Vulnerability Mechanics:**
   - CVSS scores are sampled from truncated normal distributions reflecting common CVE distributions (bimodal peaks at moderate ~5.5 and high ~8.0).
   - EPSS scores follow a log-logistic distribution with heavy skew towards lower probabilities, matching real FIRST EPSS catalog statistics.
   - CISA KEV presence is correlated with higher EPSS scores and public exploit availability.

2. **Asset Context:**
   - Asset criticality, asset types, and business services are sampled with realistic enterprise proportions.
   - Internet-exposed assets show elevated exposure weighting.

3. **Ground Truth Labeling Rule:**
   - Ground truth logit is computed via calibrated threat intelligence weights:
     $$\text{Score} = 0.35 \times \text{CVSS} + 2.5 \times \text{EPSS} + 1.8 \times \text{KEV} + 1.4 \times \text{Exposed} + \text{CriticalityWeight} + \text{AssetTypeWeight} + \epsilon$$
   - Labels are assigned via logistic probability threshold with Gaussian noise ($\epsilon \sim \mathcal{N}(0, 0.4)$) to simulate real-world uncertainty and non-deterministic event factors.

---

## 4. Limitations & Governance Guardrails

1. **Auxiliary Role:** This ML component provides an auxiliary heuristic calibration signal. It does **NOT** replace or override the deterministic Cyber Risk Engine, Financial CRQ (Open FAIR), or Monte Carlo simulations.
2. **No Loss Prediction:** This model classifies risk severity tier (`high_impact_event = 0/1`); it does **NOT** predict exact currency loss amounts.
3. **Domain Transferability:** In production deployments, this synthetic model should be fine-tuned or replaced with validated historical incident records from the customer's Security Operations Center (SOC) / SIEM data lake.
