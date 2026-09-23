# TRINETRA — Frontend Development Roadmap

## Phase 0 — Foundation

- Vite + React + TypeScript
- Tailwind, configured against `DESIGN.md` tokens (`tailwind.config.ts` + `styles/tokens.css`)
- shadcn/ui installed
- Inter font
- Global styles (`styles/globals.css`) including the reduced-motion rule
- React Router set up per the final routes (`FRONTEND_ARCHITECTURE.md` §3)
- Folder structure scaffolded

## Phase 1 — Marketing Site (this build)

Build in this order — each section is a complete vertical slice (component +
mock data + responsive + states + QA) before moving to the next:

1. `ui/` primitives — Button, Badge, MetricCard, Card
2. Navbar (desktop pill nav + mobile drawer)
3. Hero + `PipelineVisual`
4. ProblemStats
5. HowItWorks (5-stage pipeline stepper)
6. DataSources (beam diagram)
7. ProductPreview + BudgetSlider
8. CtaSection
9. Footer
10. Full-page QA pass (`QA.md`) — responsive, accessibility, motion

This is the complete Phase 1 scope. There are no additional marketing
sections beyond these — the earlier draft roadmap's longer list (separate
Risk Engine/Financial Risk/Investment Optimization sections, a "Simulation
preview" section) is superseded: those are represented inside `HowItWorks`
and `ProductPreview` respectively, per the locked decision in
`FRONTEND_CONTEXT.md`.

## Phase 2 — Product Shell (later, not this build)

```text
DashboardLayout
├── Sidebar
├── Header
├── Breadcrumbs
└── PageContainer
```

Only a `/dashboard` placeholder route ships in Phase 1. The actual shell
above is built when Phase 2 starts.

## Phase 3+ — Dashboard (later, not this build)

Overview KPIs, risk/vulnerability tables, financial risk views, investment
optimization UI, simulation UI — all deferred. See `COMPONENTS.md`'s
"Dashboard components" section for what's already specified for when this
phase begins.

## Phase 8 — Backend Integration (later)

Replace `data/demoDashboard.ts` with real calls to the Risk Engine /
Financial CRQ / Monte Carlo services once the dashboard phase connects to
them. Marketing site's static content (`problemStats`, `pipelineStages`,
`dataSources`) is never replaced by live API calls — it stays static copy.

## Phase 9 — Polish (later)

Full responsive QA, accessibility audit, motion tuning, performance pass,
visual consistency check against `DESIGN.md` — run this again at the end of
whichever phase is current, not only once.

## Vertical-Slice Rule

Prefer completing one section fully (component → mock data → responsive →
states → QA) over having many incomplete sections in progress at once.
