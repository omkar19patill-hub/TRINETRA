# TRINETRA — UI/UX Specification

## 1. Context & Goal

TRINETRA is an AI-assisted cyber-risk quantification and security investment
platform. See `FRONTEND_CONTEXT.md` for full product context and the
pipeline (CVE → Threat Intelligence → Risk → Financial Risk → Investment →
Security Action).

The UX must make complex cyber-risk decisions understandable quickly.

## 2. UX Principles

1. **Clarity over decoration** — every visual element communicates hierarchy
   or information.
2. **Risk before detail** — decision-critical signals first, then evidence.
3. **Progressive disclosure** — Summary → Explanation → Evidence.
4. **Explain important numbers** — risk scores, financial estimates, and
   demo results need context, not bare figures.
5. **One primary action per view** — avoid competing CTAs.
6. **Consistent vocabulary** — Threat, Vulnerability, Asset, Risk, Financial
   Risk, Investment, Mitigation, Simulation (see `CONTENT.md`).
7. **No fake precision** — estimated/demo values are always labeled as such.

## 3. Information Architecture — FINAL

```text
TRINETRA
├── Marketing (route: /)
│   Single scrolling page, anchor-navigated:
│   ├── #top          Hero
│   ├── #problem       Problem / Statistics
│   ├── #how-it-works    How TRINETRA Works (5-stage pipeline)
│   ├── #intelligence      Threat Intelligence / Data Sources
│   └── #platform            Product / Dashboard Preview + CTA
│
└── Product (route: /dashboard — placeholder only, later phase)
    Overview · Threat Intelligence · Vulnerabilities · Risk Analysis ·
    Financial Risk · Investment Optimization · Simulation
    (This nav applies once the dashboard is actually built. It does not
    exist as routed pages yet.)
```

There are no separate marketing routes for "How It Works" or
"Intelligence" — those are sections on the one page, reached by anchor link.

## 4. Core User Journeys

### Understanding TRINETRA (marketing, this phase)
```text
Hero (what it is, in one line)
→ Problem (why it matters, with real stats)
→ How It Works (the 5-stage pipeline)
→ Data Sources (where the numbers come from)
→ Product Preview (what using it would feel like)
→ CTA
```

### Understanding current risk (future dashboard journey — not built yet)
```text
Dashboard → Overall Risk → Top Risk Drivers → Financial Exposure
→ Highest-priority risk → Explanation / Evidence → Mitigation action
```

### Optimizing security investment (future dashboard journey — not built yet)
```text
Investment Optimization → Set budget → Review exposure → Compare controls
→ Run optimization → Review cost vs. risk reduction → Inspect rationale
```

### Dashboard screen scope — DECIDED

Seven screens are in scope for the dashboard phase, all nested under
`/dashboard` (see `FRONTEND_ARCHITECTURE.md` §3):

| Screen | Primary backend endpoints |
|---|---|
| Dashboard (overview) | `POST /optimization/run`, `GET /orchestration/assets` |
| Threat Intelligence | `GET /vulnerabilities`, `GET /vulnerabilities/{cve_id}/enriched` |
| Risk Analysis | `POST /risk/calculate`, `POST /ml/predict` |
| Financial Risk | `POST /financial-crq/calculate`, `POST /monte-carlo/simulate` |
| Investment Optimization | `POST /optimization/run`, `GET /controls` |
| What-if Simulation | `POST /optimization/before-after`, `GET /decision/{id}/marginal-budget` |
| Action Center | `GET /decision/{id}/alternatives`, `/opportunity-cost`, `/explanation` |

**Action Center** and **What-if Simulation** are in scope because both map to
stages the product pipeline already claims: Action Center is the final
"Security Action" stage in `FRONTEND_CONTEXT.md` §1, and What-if Simulation is
the promise the marketing page already makes ("Move the budget. Watch the risk
number change.").

**Continuous Monitoring is deferred.** It has no anchor in the documented
pipeline, it is the most stateful surface (time-series and polling), and it
depends on `POST /reoptimize` operating against optimization IDs held in an
in-memory store that does not survive a backend restart. It will be
reconsidered once backend persistence is decided.

## 5. Marketing Page Section Order — FINAL

```text
Navbar
Hero
Problem / Statistics
How TRINETRA Works
Threat Intelligence / Data Sources
Product / Dashboard Preview
CTA
Footer
```

## 6. Data Visualization (this phase)

| Content | Treatment |
|---|---|
| The pipeline (hero) | Custom SVG — a CVE flowing through the pipeline, not a generic workflow diagram |
| Real, sourced stats | Stat cards — big number, label, source citation |
| Data sources | Beam-converging network diagram (NVD/KEV/EPSS/ATT&CK → Risk Engine) |
| Product preview | Stylized dashboard mockup with an interactive, clearly-labeled demo slider |

Never add a chart or diagram simply to fill space.

## 7. Interaction Rules

- One primary action per major section.
- Secondary actions have lower emphasis.
- Loading states preserve layout dimensions (not applicable to static
  marketing content, but applies the moment the demo slider or any future
  API call is added).
- The demo budget slider is the one interactive control in this phase —
  it needs a visible label, an accessible name, and full keyboard operation.

## 8. Component States

Every interactive component defines: **default, hover, focus-visible,
active, disabled** (loading/error apply once real data exists). Data-driven
components (once built) additionally define: **empty, partial, stale,
overflow, long content.** See `COMPONENTS.md`.

## 9. Accessibility

Target WCAG 2.2 AA: keyboard-first operation, visible focus-visible states,
sufficient contrast, semantic HTML, accessible names, no color-only meaning,
reduced-motion support.

## 10. UX Copy

See `CONTENT.md` for full rules. In short: concise, confident, technical,
evidence-oriented. "Estimated Financial Exposure," not "Money at Risk!!!"

## 11. Empty / Error / Stale States

Reserved for the dashboard phase — the marketing site's data is static/mock
and doesn't have these states, except the demo slider, which always has a
valid default and cannot enter an error state by design.

## 12. Mobile UX

- Navbar collapses to a hamburger-triggered drawer below `md`.
- Hero's SVG pipeline visualization is hidden below `lg` (the headline and
  copy carry the section alone on mobile — see `RESPONSIVE.md`).
- Stat cards and pipeline stages stack to single/double column.
- Product preview card stacks its two columns.
- No hover-only interactions; all touch targets ≥44px.

## 13. UX Acceptance Checklist

- [ ] The pipeline (CVE → Action) is understandable within seconds of
      landing on the hero.
- [ ] Every real statistic has a visible source.
- [ ] Demo/illustrative values are clearly labeled as such.
- [ ] Focus is visible everywhere.
- [ ] Mobile behavior is defined for every section.
- [ ] Color is never the only status indicator.
