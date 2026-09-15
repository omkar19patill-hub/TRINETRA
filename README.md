TRINETRA

See Risk Before It Strikes.

TRINETRA is an AI-powered cyber risk quantification and security investment optimization platform designed to help organizations understand, prioritize, and reduce cyber risk.

It connects threat intelligence → contextual risk → financial exposure → security investment → actionable decisions in one continuous workflow.

🎯 What is TRINETRA?

Traditional cybersecurity tools often generate large numbers of vulnerabilities, alerts, and severity scores.

The real question for security leaders is:

"Which risks matter most to my organization, and where should I spend my limited security budget?"

TRINETRA aims to answer that question by combining:

Threat intelligence

Vulnerability information

Asset and business context

Exploitation likelihood

Probabilistic risk modelling

Financial risk estimation

Security investment optimization

What-if simulation

Explainable AI

Core Concept

Cyber Threat
     ↓
Contextual Risk
     ↓
Financial Exposure
     ↓
Investment Optimization
     ↓
Security Action
     ↓
Continuous Recalculation

👁️ Why "TRINETRA"?

Trinetra represents three eyes of cyber decision-making:

        TRINETRA

     👁 Threat
        +
     👁 Risk
        +
     👁 Investment

Threat

What threats and vulnerabilities are affecting the organization?

Risk

How significant is that threat for the organization's actual assets and business context?

Investment

Where should limited security resources be allocated to achieve greater expected risk reduction?

Threat + Risk + Investment = TRINETRA

🚀 Key Features

1. Continuous Risk Quantification

Continuously updates cyber risk using changing vulnerabilities, threat signals, exploitation likelihood, asset criticality, and exposure.

2. Financial Risk Estimation

Converts technical cyber exposure into probabilistic estimates of potential financial impact.

3. Explainable AI

Provides understandable explanations for risk drivers, assumptions, and recommendations.

AI is used as a decision-support layer rather than replacing the underlying risk calculations.

4. Investment Optimization

Determines how a defined cybersecurity budget can be allocated to achieve greater expected risk reduction.

5. What-if Simulation

Allows users to compare different security investment scenarios before making a decision.

Example:

Budget: ₹10,00,000

Option A
Patch critical vulnerability
        ↓
Expected Risk Reduction: X

Option B
Deploy additional security control
        ↓
Expected Risk Reduction: Y

TRINETRA
        ↓
Compare scenarios
        ↓
Recommend the better allocation

🧠 How TRINETRA Works

┌─────────────────────────┐
│   THREAT INTELLIGENCE   │
│                         │
│ NVD • CISA KEV • EPSS  │
│ MITRE ATT&CK            │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│      RISK ENGINE        │
│                         │
│ Threat                  │
│ Vulnerability           │
│ Asset Context           │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     FINANCIAL RISK      │
│                         │
│ Estimated Loss          │
│ Statistical Simulation  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ INVESTMENT OPTIMIZATION │
│                         │
│ Budget                  │
│ Risk Reduction          │
│ Optimal Allocation      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     SECURITY ACTION     │
│                         │
│ Prioritize              │
│ Mitigate                │
│ Monitor                 │
└─────────────────────────┘

🤖 AI / ML Decision Support

TRINETRA separates core risk calculations from AI-generated explanations.

ML Modelling

Used where data-driven modelling can improve threat or risk analysis.

Statistical Simulation

Used to represent uncertainty and estimate potential financial exposure.

Explainable AI

Used to translate analytical results into understandable recommendations.

Risk Data
    ↓
Deterministic / Quantitative Models
    ↓
Probabilistic Analysis
    ↓
Optimization
    ↓
AI Explanation
    ↓
Human Decision

The LLM is not the core risk calculator.

This separation helps keep the system more transparent, auditable, and defensible.

🏗️ System Architecture

┌──────────────────┐
│ Threat           │
│ Intelligence     │
│                  │
│ NVD              │
│ CISA KEV         │
│ EPSS             │
│ MITRE ATT&CK     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Data Ingestion   │
│ & Normalization  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Risk Engine      │
│                  │
│ Threat           │
│ Vulnerability    │
│ Asset Context    │
│ Exposure         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Financial Risk   │
│ & Simulation     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Investment       │
│ Optimization     │
│                  │
│ Budget           │
│ Risk Reduction   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ AI Explanation   │
│ & Decision       │
│ Support          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ TRINETRA         │
│ Dashboard        │
└──────────────────┘

🛠️ Technology Stack

Layer

Technology

Frontend

React.js

Styling

Tailwind CSS

Backend

Python + FastAPI

Data Processing

Pandas + NumPy

Machine Learning

Scikit-learn

Statistical Modelling

SciPy / NumPy

Optimization

Google OR-Tools

Database

PostgreSQL

Containerization

Docker

The stack may evolve as the MVP develops.

📊 Data Sources

TRINETRA is designed to work with publicly available cybersecurity intelligence during the MVP stage.

Source

Purpose

NVD

Vulnerability and CVE information

CISA KEV

Known exploited vulnerabilities

EPSS

Vulnerability exploitation probability

MITRE ATT&CK

Adversary tactics and techniques

Organization Data

Assets, criticality, exposure and business context

Synthetic Data

MVP testing when private enterprise data is unavailable

Private organizational data can be integrated as the platform evolves.

💰 Investment Optimization

One of TRINETRA's core objectives is to move from:

"What vulnerabilities exist?"

to:

"Where should we invest?"

The optimization engine considers:

Available security budget

Candidate security controls

Risk associated with assets

Expected risk reduction

Cost of controls

Different investment scenarios

Conceptually:

        Security Budget
              │
              ▼
    ┌──────────────────┐
    │ Candidate        │
    │ Security Actions │
    └────────┬─────────┘
             │
             ▼
     Estimate Risk
       Reduction
             │
             ▼
     Compare Scenarios
             │
             ▼
      Optimal Allocation

🔮 What-if Simulation

TRINETRA allows security teams to explore alternative investment decisions.

Example questions:

"What if we increase the security budget?"

"What if we patch this vulnerability first?"

"What if we deploy this security control?"

"What if we choose Control A instead of Control B?"

"Which investment gives greater expected risk reduction?"

The goal is to make cybersecurity investment decisions evidence-based and budget-aware.

🎯 Target Users

TRINETRA is intended for organizations that need to make risk-based cybersecurity investment decisions.

Primary Users

CISOs

Security Operations Teams

Enterprise Security Teams

Risk Management Teams

Regulated Industries

Government Organizations

Critical Infrastructure Operators

📈 Long-Term Vision

TRINETRA is designed to evolve from an SIH MVP into a scalable cyber risk decision platform.

SIH MVP
   ↓
Enterprise Integration
   ↓
Multi-Organization Platform
   ↓
Government / Critical Infrastructure

Future capabilities may include:

Enterprise asset integrations

Real-time threat intelligence

Advanced probabilistic risk models

Improved financial risk modelling

Security control effectiveness modelling

Automated risk reporting

Advanced investment optimization

Multi-organization risk management

🧪 Current Project Status

Status: 🚧 MVP Under Development

Current development focus:

Project foundation

Database schema

Threat intelligence ingestion

Vulnerability normalization

Asset and business context modelling

Initial risk engine

Financial risk model

Investment optimization

What-if simulation

Explainable AI layer

Web dashboard

Testing

Deployment

📁 Project Structure

The project will follow a modular architecture.

trinetra/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── services/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── core/
│   │
│   └── tests/
│
├── risk-engine/
│   ├── scoring/
│   ├── modelling/
│   ├── simulation/
│   └── optimization/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
│
├── docs/
│
├── docker/
│
├── .gitignore
├── README.md
└── LICENSE

🔐 Security & Responsible Use

TRINETRA is designed as a cyber risk decision-support platform.

It does not aim to replace:

Security professionals

Risk managers

Incident response teams

Organizational governance

Professional security assessments

Financial outputs should be interpreted as probabilistic estimates based on available data and assumptions, not guaranteed predictions of actual losses.

🏆 Built for Smart India Hackathon 2026

TRINETRA is being developed as part of Smart India Hackathon 2026.

Problem Statement

AI-Powered Continuous Cyber Risk Quantification and Investment Optimization Platform

Core Objective

Move from Cyber Threat → Risk → Financial Impact → Optimal Security Investment.

👥 Team

Team Vajra

📜 License

This project is currently under active development.

License information will be added as the project matures.

⭐ Vision

See Risk Before It Strikes.

TRINETRA aims to help organizations move from reactive vulnerability management toward continuous, quantitative, financially informed, and optimized cybersecurity decision-making.
