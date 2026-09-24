# TRINETRA — Frontend Architecture

## 1. Stack

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- React Router
- TanStack Query (reserved for when the dashboard connects to the real backend — not needed for the marketing phase)
- Recharts (dashboard phase)
- Lucide React

Keep dependencies minimal. **No animation library** — see `ANIMATION.md` for
why plain CSS + one small custom hook covers everything the marketing site
needs.

## 2. Folder Structure

```text
Frontend/
├── public/
│   ├── fonts/
│   └── images/
├── docs/                      ← this documentation pack
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── ui/                 Button, Badge, MetricCard, Card
│   │   ├── layout/               PageContainer, Section
│   │   ├── navigation/             Navbar, MobileNav
│   │   └── marketing/
│   │       ├── Hero.tsx
│   │       ├── PipelineVisual.tsx      (hero SVG: CVE → stages)
│   │       ├── ProblemStats.tsx
│   │       ├── HowItWorks.tsx           (5-stage pipeline stepper)
│   │       ├── DataSources.tsx           (NVD/KEV/EPSS/ATT&CK beam diagram)
│   │       ├── ProductPreview.tsx
│   │       ├── BudgetSlider.tsx
│   │       ├── CtaSection.tsx
│   │       └── Footer.tsx
│   ├── pages/
│   │   ├── marketing/
│   │   │   └── Home.tsx          (composes all marketing/ sections, in order)
│   │   └── dashboard/
│   │       └── Placeholder.tsx   (Phase 2+, not built yet)
│   ├── layouts/
│   │   ├── MarketingLayout.tsx
│   │   └── DashboardLayout.tsx   (shell only, not built yet)
│   ├── hooks/
│   │   └── useInView.ts          (IntersectionObserver-based reveal hook)
│   ├── lib/
│   ├── data/                     mock data — see MOCK_DATA.md
│   ├── types/
│   ├── config/
│   ├── styles/
│   │   ├── globals.css
│   │   └── tokens.css            DESIGN.md tokens as CSS custom properties
│   ├── App.tsx
│   └── main.tsx
├── .env.example
├── package.json
└── vite.config.ts
```

Note the capitalized `Frontend/` — this matches the actual repository, not
the lowercase placeholder shown in the root `README.md`'s illustrative tree.

## 3. Routes — FINAL

```text
/              Marketing home (single scrolling page, anchor-nav sections)
/dashboard     Placeholder route only — not implemented this phase
*              404
```

No separate routes for `/how-it-works`, `/intelligence`, etc. Those are
in-page anchors (`#problem`, `#how-it-works`, `#intelligence`, `#platform`)
within the single `Home` page, using native smooth scroll:

```css
html { scroll-behavior: smooth; }
section { scroll-margin-top: <navbar height>; }
```

No routing library beyond React Router's basic setup is required for this.

## 4. Component Architecture

Components are reusable, typed, accessible, responsive, and state-aware.
Presentational components (`marketing/`, `ui/`) hold no unrelated business
logic — the budget slider's math lives in `data/demoDashboard.ts`
(see `MOCK_DATA.md`), not inside `BudgetSlider.tsx` itself.

`components/ui/` is shared between the marketing site now and the dashboard
later — build these primitives (Button, Badge, MetricCard, Card) to the
`DESIGN.md` spec exactly, since rework here is expensive later.

## 5. Data Architecture

```text
UI
 ↓
data/ (typed mock modules)
```

No live API calls in this phase. `src/data/` holds every value the marketing
site displays — real/sourced stats and illustrative demo data alike, clearly
distinguished (see `MOCK_DATA.md`). Nothing lives inline in JSX.

## 6. API Boundary (backend exists — no frontend integration this phase)

An earlier draft of this section listed a suggested `/api/*` boundary
(`/api/dashboard`, `/api/threats`, `/api/risks`, …). **Those endpoints do not
exist.** They were a proposal, never implemented, and building against them
would produce a frontend that cannot talk to this backend.

The routes below are the ones **actually implemented** in `Backend/`, verified
against the running application's OpenAPI schema. There is no `/api` prefix, and
most are `POST` because they take input data rather than returning a fixed
resource.

### Implemented — core pipeline

```text
POST /risk/calculate              deterministic risk score from CVSS/EPSS/KEV/exposure
POST /financial-crq/calculate     Open FAIR loss magnitude and Expected Annual Loss
POST /monte-carlo/simulate        stochastic loss distribution (P50/P75/P90/P95/P99)
POST /monte-carlo/from-crq        run a simulation directly from a CRQ result
GET  /controls                    security control catalog
POST /controls/assess             assess controls against an asset
POST /controls/resolve-dependencies
POST /optimization/run            budget-constrained control selection (main entry point)
POST /optimization/before-after   baseline vs post-control comparison
```

### Implemented — decision intelligence

```text
GET  /decision/optimizations
POST /decision/register
GET  /decision/{optimization_id}/alternatives
GET  /decision/{optimization_id}/opportunity-cost
GET  /decision/{optimization_id}/marginal-budget
GET  /decision/{optimization_id}/explanation
```

These return 404 when an optimization ID is unknown. They do **not** silently
fall back to benchmark data; pass `demo_mode=true` to opt into it explicitly.

### Implemented — threat intelligence, ML, AI, provenance, orchestration

```text
GET  /vulnerabilities
GET  /vulnerabilities/{cve_id}/enriched
POST /vulnerabilities/risk-engine-payload
POST /ingestion/vulnerability/{cve_id}/refresh
POST /ingestion/bulk-sync
GET  /ingestion/status

POST /ml/predict
GET  /ml/model-info

POST /ai/explain-risk
POST /ai/explain-optimization
POST /ai/explain-scenario
POST /ai/query

POST /blockchain/record
GET  /blockchain/verify/{assessment_id}
GET  /blockchain/records
GET  /blockchain/receipts

POST /reoptimize
POST /recalculate/{asset_id}
GET  /orchestration/assets
```

Health endpoints exist per module (`/risk/health`, `/financial-crq/health`,
`/monte-carlo/health`, `/decision/health`, `/ml/health`, `/ai/health`,
`/blockchain/health`, `/ingestion/health`, `/orchestration/health`), plus `GET /`
for service metadata and `/docs` / `/redoc` for interactive API documentation.

### Not implemented

There is no aggregated dashboard endpoint. A dashboard view must compose data
from the routes above — `POST /optimization/run` is the closest single call,
returning risk, financial loss and selected controls together.

### Control identifiers

`selected_controls` and `rejected_controls` contain stable control IDs
(`CTRL-MFA`, `CTRL-EDR`, …), consistently across `/optimization/run` and
`/decision/{id}/alternatives`. Human-readable names are available separately in
`control_explanations[].control`, alongside `control_explanations[].control_id`.

No frontend integration happens in this phase — `src/` currently contains no
API calls. This section exists so that when integration begins, it targets the
real contract.

## 7. State

- React local state: tabs, dropdowns, modals, the demo budget slider value.
- TanStack Query: reserved for the dashboard phase once it talks to a real
  API. Not needed for static/mock marketing content.
- No global state store for this phase.

## 8. Type Safety

Avoid `any`. Example:

```ts
type RiskLevel = "critical" | "high" | "medium" | "low";

interface DemoRiskResult {
  budgetLakhs: number;
  riskScore: number;
  riskLevel: RiskLevel;
  riskReductionPct: number;
  exposureCr: number;
}
```

See `MOCK_DATA.md` for the full type list.

## 9. Environment

```text
VITE_API_BASE_URL=   # unused this phase — reserved for dashboard integration
```

Never commit secrets.

## 10. Definition of Done

A feature is complete only when:
- desktop works
- mobile works
- loading/empty/error states exist where applicable
- keyboard navigation works
- focus is visible
- `prefers-reduced-motion` is respected
- TypeScript passes
- lint/build passes
