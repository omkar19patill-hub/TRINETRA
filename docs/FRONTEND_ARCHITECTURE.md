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

## 6. API Boundary (future — not built this phase)

Suggested, not binding, for when the dashboard phase begins:

```text
GET  /api/dashboard
GET  /api/threats
GET  /api/vulnerabilities
GET  /api/risks
GET  /api/financial-risk
GET  /api/investments
POST /api/simulate
```

The real backend (Risk Engine, Financial CRQ, Monte Carlo) already exists as
separate services — see the repo's backend `README.md` files — but no
frontend integration happens in this phase.

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
