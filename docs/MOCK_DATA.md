# TRINETRA — Mock Data Architecture

## Principle

Two categories of data appear on the marketing site. They must never be
visually or structurally ambiguous to the viewer:

1. **Real, sourced data** — the four Problem-section statistics. Cited,
   accurate, never changes based on user interaction.
2. **Illustrative demo data** — the Product Preview's risk score, exposure,
   and budget-slider output. Clearly labeled "demo data" wherever shown.
   Interactive, but not connected to any real backend this phase.

Never let these two blur together. A viewer must always be able to tell
which numbers are real and which are illustrative.

## File Layout

```text
src/data/
├── problemStats.ts     Real, cited statistics
├── pipelineStages.ts     The 5 How-It-Works stages
├── dataSources.ts          NVD / CISA KEV / EPSS / MITRE ATT&CK descriptions
└── demoDashboard.ts          Budget-slider math (pure function)

src/types/
└── marketing.ts    Shared interfaces for all of the above
```

## `types/marketing.ts`

```ts
export interface StatCard {
  value: string;        // display-formatted, e.g. "29,44,248"
  label: string;         // one-line context
  source: string;          // citation, e.g. "CERT-In, Govt. of India"
}

export interface PipelineStage {
  index: number;          // 1-5
  title: string;
  description: string;
}

export interface DataSource {
  name: string;           // "NVD"
  description: string;
}

export type RiskLevel = "critical" | "high" | "medium" | "low";

export interface DemoRiskResult {
  budgetLakhs: number;
  riskScore: number;         // 0-100
  riskLevel: RiskLevel;
  riskReductionPct: number;  // 0-100
  exposureCr: number;        // ₹ crore
}
```

## `problemStats.ts` — real, cited

```ts
import { StatCard } from "../types/marketing";

export const problemStats: StatCard[] = [
  {
    value: "29,44,248",
    label: "Cyber incidents in India, 2025 — up from 20,41,360 in 2024",
    source: "CERT-In, Govt. of India",
  },
  {
    value: "31%",
    label: "Of breaches began with an exploited software vulnerability",
    source: "Verizon 2026 DBIR",
  },
  {
    value: "263%",
    label: "Growth in CVE submissions between 2020 and 2025",
    source: "NIST",
  },
  {
    value: "₹22 Cr",
    label: "Average cost of a data breach in India, 2025",
    source: "IBM Cost of a Data Breach",
  },
];
```

Do not add, remove, or reword these without a citable source. See
`CONTENT.md` for the no-fake-precision rule.

## `pipelineStages.ts`

```ts
import { PipelineStage } from "../types/marketing";

export const pipelineStages: PipelineStage[] = [
  { index: 1, title: "Threat Intelligence", description: "Live CVE, EPSS and KEV data mapped to your actual assets." },
  { index: 2, title: "Risk Analysis", description: "Likelihood and business impact combined into one score." },
  { index: 3, title: "Financial Risk", description: "Converted into an estimated ₹ exposure range — not a single guess." },
  { index: 4, title: "Investment Optimization", description: "A fixed budget, allocated for maximum risk reduction." },
  { index: 5, title: "Security Action", description: "Fix, mitigate, accept, or transfer — with the reasoning attached." },
];
```

## `dataSources.ts`

```ts
import { DataSource } from "../types/marketing";

export const dataSources: DataSource[] = [
  { name: "NVD", description: "Vulnerability data, CVSS severity, affected products." },
  { name: "CISA KEV", description: "Confirmed, real-world exploitation signal." },
  { name: "EPSS", description: "Probability of exploitation in the next 30 days." },
  { name: "MITRE ATT&CK", description: "Adversary tactics and techniques, for context." },
];
```

## `demoDashboard.ts` — illustrative only

Ported directly from the validated prototype's inline JS, as a typed pure
function. This is deliberately named `computeDemoRisk`, not
`computeRisk` — nobody should mistake it for the real risk engine.

```ts
import { DemoRiskResult, RiskLevel } from "../types/marketing";

const BASE_RISK_SCORE = 72;
const BASE_EXPOSURE_CR = 18.4;

export function computeDemoRisk(budgetLakhs: number): DemoRiskResult {
  const reduction = Math.min(
    78,
    Math.round(12 + 66 * (1 - Math.exp(-budgetLakhs / 45)))
  );
  const riskScore = Math.max(18, Math.round(BASE_RISK_SCORE - reduction * 0.62));
  const exposureCr = Math.max(3.2, Number((BASE_EXPOSURE_CR * (1 - reduction / 100)).toFixed(1)));

  let riskLevel: RiskLevel = "low";
  if (riskScore >= 75) riskLevel = "critical";
  else if (riskScore >= 50) riskLevel = "high";
  else if (riskScore >= 25) riskLevel = "medium";

  return { budgetLakhs, riskScore, riskLevel, riskReductionPct: reduction, exposureCr };
}
```

`BudgetSlider.tsx` calls this on every `input` event and renders the result
— it holds no math of its own.

## When the Real Backend Connects (later phase, not now)

`problemStats.ts`, `pipelineStages.ts`, and `dataSources.ts` are static
content and stay as-is indefinitely — they're marketing copy, not live data.
`demoDashboard.ts` is the one file that gets replaced wholesale once the
dashboard phase wires up the real Risk Engine / Financial CRQ / Monte Carlo
services — at that point `computeDemoRisk` is deleted, not extended.
