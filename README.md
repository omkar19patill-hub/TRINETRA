# TRINETRA

### AI-Powered Continuous Cyber Risk Quantification & Investment Optimization Platform

> **SIH26105** &middot; Smart India Hackathon 2026 &middot; Theme: Blockchain & Cybersecurity &middot; Sponsor: AICTE Cyber Security Cell

🚧 **Work in Progress — built for SIH 2026**

---

## The Problem

Organizations face thousands of vulnerabilities but can only fix a few, and CVSS scores tell you how severe a flaw is — not how likely it is to be exploited, which business asset it threatens, or what it would actually cost. Risk assessments are typically a once-a-year PDF, disconnected from the board's financial language, and security budgets get spent on a ranked list instead of an actual investment plan.

**Trinetra turns raw threat data into a continuously updated, board-ready decision: where should the next rupee of security budget go?**

## What Trinetra Does

```
Cyber Threat Intelligence  →  Risk Analysis  →  Financial Risk  →  Investment Optimization  →  Security Action
 (CVE/NVD, KEV, EPSS,          (likelihood ×      (₹ exposure,       budget-constrained          (Fix / Mitigate /
  asset & business context)     exposure)          via Open FAIR)     allocation across controls)   Accept / Transfer)
```

## Key Features

| Feature | What it does |
|---|---|
| **Continuous Risk Quantification** | Risk score recalculates automatically as new CVE, KEV, and EPSS data arrives |
| **Financial Risk Estimation** | Converts findings into an estimated ₹ exposure range, not a single guessed number |
| **Explainable AI** | Plain-language narrative explains why a score changed, with every assumption traceable |
| **Investment Optimization** | Allocates a fixed security budget across controls to maximize risk reduction |
| **What-if Simulation** | Test "cut budget by X%" or "fix this first" before committing real spend |

## System Architecture

```mermaid
flowchart TD
    A["Data Sources<br/>NVD · CISA KEV · EPSS · MITRE ATT&CK · Asset & Business Context"] --> B["Data Ingestion Layer<br/>(scheduled API pollers)"]
    B --> C["Data Processing / Normalization<br/>(CVE → asset → business unit)"]
    C --> D["Risk Engine<br/>Loss Event Frequency × Loss Magnitude, Monte Carlo"]
    D --> E["Financial Risk / Simulation Layer<br/>Annualized Loss Expectancy range"]
    E --> F["Investment Optimization Engine<br/>Budget-constrained allocation (LP/knapsack)"]
    F --> G["AI Explanation Layer<br/>Narrates output — does NOT calculate risk"]
    G --> H["Dashboard<br/>Risk Score · ₹ Exposure · Recommended Actions"]
```

**Component split:**
- **Deterministic/rule-based:** CVE-to-asset mapping, control-to-risk mapping, budget constraint logic
- **Probabilistic/statistical:** Loss frequency & magnitude distributions, Monte Carlo simulation
- **AI/LLM:** Narrative explanation and board-ready summaries only — never the core ₹ calculation
- **Optimization engine:** LP/integer programming solver for budget allocation

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js + Tailwind CSS |
| Backend | Python (FastAPI) |
| AI/ML | LLM API (explanation, asset-to-CVE mapping) + scikit-learn/PyMC |
| Database | PostgreSQL + Redis |
| Optimization | SciPy / PuLP |
| Deployment | Docker, cloud free-tier (AWS/GCP/Azure) |

## Data Sources

| Source | Provides | Access |
|---|---|---|
| [NVD](https://nvd.nist.gov) | CVE details, CVSS, CWE, CPE | Public / free (API) |
| [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) | Confirmed actively-exploited CVEs | Public / free |
| [FIRST EPSS](https://www.first.org/epss) | Probability of exploitation (next 30 days) | Public / free (API) |
| [MITRE ATT&CK](https://attack.mitre.org) | Adversary tactics/techniques mapping | Public / free |
| Synthetic org/asset data | Fills the gap where real enterprise asset & financial data is private | Self-generated, clearly labeled as illustrative |

## Project Structure

```
trinetra/
├── frontend/              # React + Tailwind dashboard
├── backend/
│   └── app/
│       ├── ingestion/      # NVD / CISA KEV / EPSS pollers
│       ├── risk_engine/    # Open FAIR-based quantification, Monte Carlo
│       ├── optimization/   # Budget-constrained solver
│       ├── explanation/    # LLM narrative layer
│       └── api/
├── docker-compose.yml
├── docs/                   # research references, architecture notes
└── README.md
```
*(Adjust to match your actual layout — this is the structure implied by the tech stack above.)*

## Getting Started

**Prerequisites:** Node.js 18+, Python 3.11+, Docker (optional, for full-stack run)

```bash
# Clone the repo
git clone https://github.com/<your-org>/trinetra.git
cd trinetra

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set DATABASE_URL, REDIS_URL, LLM_API_KEY
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Or run the full stack with Docker:
```bash
docker-compose up --build
```

## Roadmap

```
SIH MVP → Enterprise Integration (real asset inventory/CMDB, SIEM)
        → Multi-Organization (MSSP/insurer view across clients)
        → Government / Critical Infrastructure (sector-wide risk visibility)
```

## Team


## References

- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [NIST SP 800-30 Rev.1 — Guide for Conducting Risk Assessments](https://csrc.nist.gov/pubs/sp/800/30/r1/final)
- [Open FAIR, The Open Group / FAIR Institute](https://www.fairinstitute.org/about)
- Tsiodra, Panda, Chronopoulos & Panaousis, *"Cyber Risk Assessment and Optimization,"* IEEE Access, 2023 — [doi.org/10.1109/ACCESS.2023.3272670](https://doi.org/10.1109/ACCESS.2023.3272670)

## License

No license has been selected yet. For a hackathon/academic project, [MIT](https://choosealicense.com/licenses/mit/) is a common default — add a `LICENSE` file once the team decides.

## Acknowledgments

Built on public data and standards from NIST, CISA, FIRST.org, MITRE, and The Open Group / FAIR Institute.
