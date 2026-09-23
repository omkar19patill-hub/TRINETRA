# TRINETRA — Component Specification

Components are split into two groups. **Marketing** components are built
this phase. **Dashboard** components are specified for later and should not
be built yet — listed here only so the shared `ui/` primitives are designed
with both in mind.

---

## Marketing components (build now)

### Navbar
Floating pill nav, fixed position, backdrop-blur. Logo (left), anchor links
(center, desktop only), primary CTA (right), hamburger toggle (mobile).
States: default, link-hover, mobile-menu-open/closed.

### Hero
Two-column on `lg`+ (copy left, `PipelineVisual` right), single column with
visual hidden below `lg`. Contains: eyebrow badge, headline, subhead, two
CTAs, a small trust line (data-source credit).

### PipelineVisual
The hero SVG. Shows a CVE node flowing along an animated path through a Risk
Score node to a Financial Exposure node — TRINETRA's actual pipeline, not a
generic workflow. See `ANIMATION.md` for the exact motion spec and a
documented implementation gotcha (CSS `transform` animations on an SVG
element with a `transform` attribute can silently override that attribute —
nest the animated element inside a separately-positioned wrapper `<g>`).

### ProblemStats
Grid of `MetricCard`s (2-col mobile, 4-col desktop). Each card: big number,
one-line context, source citation. Every number here must be real and cited
— see `MOCK_DATA.md`.

### HowItWorks
5-column (desktop) / stacked (mobile) stepper representing the pipeline:
Threat Intelligence → Risk → Financial Risk → Investment Optimization →
Security Action. Each step: index, title, one-line description. This is
where Risk Engine, Financial Risk, and Investment Optimization live — not as
separate sections.

### DataSources
Two-column: left is a definition list (NVD, CISA KEV, EPSS, MITRE ATT&CK),
right is a beam-converging SVG diagram (four source badges converging on a
central "Risk Engine" node).

### ProductPreview
A stylized browser-chrome card containing a mock dashboard: risk score card,
financial exposure card, and the `BudgetSlider`.

### BudgetSlider
The one interactive control in the marketing site. A range input bound to
`computeDemoRisk()` (see `MOCK_DATA.md`) that updates risk score, risk
level, and exposure live. Must have a visible label, an `aria-label`, and
full keyboard operability. Output values must carry a "demo data" label
(see `CONTENT.md`).

### CtaSection
Centered closing statement + one primary button.

### Footer
Logo, tagline, section links, data-source credits, project/team credit line,
copyright.

---

## Shared UI primitives (`components/ui/`)

Build to spec now — reused by the dashboard later.

### Button
- **Primary:** high contrast, the conic-gradient hover reveal is reserved
  for this variant only.
- **Secondary:** bordered.
- **Ghost:** minimal, tertiary actions.
States: default, hover, focus-visible, active, disabled, loading.

### Badge / StatusBadge
Text + visual cue, never color alone. Variants: critical, high, medium, low,
success, neutral. Text is mandatory.

### MetricCard
```text
Label
Primary value
Supporting context
Source (if a real stat) or "Demo data" (if illustrative)
```

### Card
Generic bordered surface — the base every other card composes from.

---

## Component state contract (applies to every interactive component)

```text
default · hover · focus-visible · active · disabled · loading · error · empty (data-driven only)
```

---

## Dashboard components (specified, NOT built this phase)

Listed for forward compatibility of the `ui/` primitives only.

**Navigation:** Sidebar, Breadcrumbs, Tabs
**Data:** DataTable, TrendIndicator, EmptyState, ErrorState, LoadingSkeleton
**Risk:** RiskOverview, RiskDriverList, RiskBreakdown, SeverityBadge, AssetRiskCard, VulnerabilityRow
**Financial:** FinancialExposureCard, LossDistribution, EstimatedLossChart, ScenarioComparison
**Investment:** BudgetInput, InvestmentOption, OptimizationResult, RiskReductionCard
**Simulation:** SimulationForm, ScenarioSlider, BeforeAfterPanel, SimulationResult

Do not scaffold empty files for these yet — build them when the dashboard
phase actually starts, against real data contracts.

---

## Icon rules

Use icons only when they improve recognition. Do not put an icon beside
every label, use decorative cyber icons everywhere, or replace meaningful
text with ambiguous icons. Icon-only interactive controls require accessible
names.
