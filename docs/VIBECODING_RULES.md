# TRINETRA — Frontend Vibecoding Rules

## Role

The AI coding agent (Antigravity) acts as a senior frontend engineer inside
the TRINETRA repository. The goal is production-quality code, not generic
demo UI.

## Before Coding — Required Reading

Always read first:
```text
FRONTEND_CONTEXT.md
FRONTEND_ARCHITECTURE.md
```

Then read only what's relevant to the current task:
```text
DESIGN.md              — before touching styling/tokens
UI_UX.md                — before building a new section's structure
COMPONENTS.md             — before creating any component
ANIMATION.md                — before adding any motion
RESPONSIVE.md                 — before writing breakpoint-specific code
CONTENT.md                       — before writing any copy
MOCK_DATA.md                        — before touching src/data/
QA.md                                   — before marking a task complete
DEVELOPMENT_ROADMAP.md                     — to confirm build order
```

(This list was previously incomplete — an earlier draft only listed
DESIGN/UI_UX/COMPONENTS/RESPONSIVE/ANIMATION/CONTENT and omitted the
architecture, roadmap, and QA docs. This version is the correct, complete
list.)

Also inspect: existing files in `Frontend/src/`, `package.json`, current
routing, existing components, design tokens already in `styles/tokens.css`,
and this repo's root `README.md`. Never overwrite existing work without
understanding it.

## The Prototype Is Frozen

A visual prototype has been validated and is the visual reference for this
entire build. **Do not redesign it. Do not propose a different visual
direction.** The job is to rebuild it correctly as typed, componentized
React — matching its look, content, and motion — not to reinterpret it.

## Coding Rules

- Preserve TypeScript strictness. Avoid `any`.
- Reuse components — check `COMPONENTS.md` before creating a new one.
- Reuse semantic tokens from `DESIGN.md` / `tokens.css` — never a raw hex
  value in a component file.
- Avoid duplicated styles or arbitrary spacing values.
- Avoid unnecessary dependencies — in particular, no animation library (see
  `ANIMATION.md` for why plain CSS + `useInView` covers this build).
- Keep components focused; keep the budget-slider math in
  `data/demoDashboard.ts`, not inside the component.

## Product-Quality Rule

Never generate a generic SaaS/cyber dashboard. The interface must
communicate TRINETRA's actual pipeline:

```text
CVE → Threat Intelligence → Risk → Financial Risk → Investment → Security Action
```

## Routing Is Locked

```text
/              Marketing home (single page, anchor nav)
/dashboard     Placeholder only
*              404
```

Do not split marketing content into separate routes. If a task seems to
require it, stop and flag the conflict rather than deciding silently — this
mirrors the same discipline the backend's `AGENTS.md` uses for architecture
changes.

## Major Changes

Explain before making broad changes to: routing, state architecture,
dependencies, the API boundary, folder structure, or design tokens. All of
these are currently locked per `FRONTEND_CONTEXT.md` — changing any of them
is an architectural decision, not an implementation detail.

## Iteration Loop

```text
1. Inspect
2. Plan
3. Implement
4. Run/check
5. Fix
6. Summarize changed files
```

Do not make a large batch of unrelated changes in one pass. Follow the
vertical-slice build order in `DEVELOPMENT_ROADMAP.md`.

## No Placeholder Slop

Avoid lorem ipsum, random fake metrics, meaningless icons, stock cyber
imagery, fake testimonials, generic AI copy, unnecessary sections. Every mock
value in `src/data/` must be either real and cited (`problemStats.ts`) or
explicitly, visibly labeled as demo data (`demoDashboard.ts` output) — see
`MOCK_DATA.md`.

## Completion

A feature is complete only when it satisfies `FRONTEND_ARCHITECTURE.md`
§10's Definition of Done and passes the relevant items in `QA.md`.
