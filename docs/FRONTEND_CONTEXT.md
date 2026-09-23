# TRINETRA — Frontend Context

**Read this file first.** It is the single source of truth for decisions that
used to be open questions across the other documents. If another document
says something different from this file, this file is correct.

---

## 1. What TRINETRA Is

TRINETRA is an AI-powered continuous cyber risk quantification and investment
optimization platform, built for **SIH26105** (Smart India Hackathon 2026,
theme: Blockchain & Cybersecurity, sponsor: AICTE Cyber Security Cell).

**Tagline:** See Risk Before It Strikes.

**The problem:** organizations face thousands of vulnerabilities but can only
fix a few. CVSS tells you how severe a flaw is — not how likely it is to be
exploited, which asset it threatens, or what it would actually cost. Risk
assessments are typically a once-a-year PDF, disconnected from the language a
board spends money in.

**What TRINETRA does:** turns raw vulnerability data into a continuously
updated, rupee-denominated risk number, and tells the organization exactly
where the next rupee of security budget should go.

**The pipeline** (this is the spine of the entire product and every piece of
marketing content should trace back to it):

```
CVE
 ↓
Threat Intelligence      (NVD, CISA KEV, EPSS, MITRE ATT&CK)
 ↓
Risk                       (likelihood × business impact)
 ↓
Financial Risk ₹             (estimated exposure, via Open FAIR)
 ↓
Investment Optimization        (budget-constrained control allocation)
 ↓
Security Action                   (Fix / Mitigate / Accept / Transfer)
```

## 2. Current Phase

We are building the **marketing frontend only** — a single scrolling landing
page. The product dashboard (the actual risk/financial/investment UI) is a
later phase and is not part of this build. See §4.

The backend (Risk Engine, Financial CRQ, Monte Carlo simulation, threat-intel
ingestion) already exists as separate services but is **not wired to the
frontend yet**. This phase uses mock data exclusively — see `MOCK_DATA.md`.

## 3. Visual Reference

A visual prototype has been built and validated — a single self-contained
HTML/Tailwind/vanilla-JS page. **It is frozen as the visual reference.**

**File location:** `Frontend/docs/prototype.html` — open it directly in a
browser (no build step needed) to see the approved visual reference.

- Do not redesign it.
- Do not introduce a different visual direction while implementing it in React.
- The job now is to rebuild it correctly as typed, componentized React —
  same look, same content, same motion, production architecture.

If something in this documentation pack seems to contradict what the
prototype actually looks like, the prototype's validated visual behavior
wins for *appearance*; this pack wins for *how it's built*.

## 4. Locked Decisions

These were open questions in earlier drafts. They are now closed.

### Routing
```
/              Marketing home — single continuous scrolling page, anchor navigation
/dashboard     Placeholder route only. Not implemented this phase.
*              404
```
The marketing site is **one page**, not split into `/how-it-works`,
`/intelligence`, etc. Section navigation uses in-page anchors
(`#problem`, `#how-it-works`, `#intelligence`, `#platform`) with smooth
scroll — no routed sub-pages for marketing content.

### Design tokens — accent color
```
accent.primary = #3355FF
```
Sourced from the TRINETRA logo mark. This is final — do not treat it as
provisional. Severity accents are also finalized; see `DESIGN.md` §3.

### Marketing page structure
```
Navbar
Hero
Problem / Statistics
How TRINETRA Works        (5-stage pipeline — see §1)
Threat Intelligence / Data Sources
Product / Dashboard Preview
CTA
Footer
```
Risk Engine, Financial Risk, and Investment Optimization are represented
**inside** the 5-stage "How TRINETRA Works" pipeline as steps — not as three
separate full-width marketing sections. This was a deliberate compression
decision, confirmed final.

### Hero visualization
The hero must visualize TRINETRA's actual pipeline (a CVE flowing through
Threat Intelligence → Risk → Financial Risk → Investment) — never a generic
"AI workflow" animation. This is a non-negotiable brand differentiator: the
whole point of TRINETRA is that it's specific to cyber risk, not a
skinned template.

## 5. What to Avoid

Carried forward from the validated prototype and non-negotiable:

- No generic SaaS/cybersecurity visual clichés (shields on every card, hacker
  green, stock cyber imagery)
- No excessive gradients or neon glow
- No decorative icons that don't aid recognition
- No AI-slop UI — no unnecessary sections, no lorem ipsum, no fake
  testimonials, no meaningless motion
- No unlabeled demo/illustrative data — see `MOCK_DATA.md` and `CONTENT.md`

## 6. Where to Go Next

| If you need... | Read... |
|---|---|
| Colors, type, spacing, radius, motion durations | `DESIGN.md` |
| Page structure, journeys, states, accessibility | `UI_UX.md` |
| Tech stack, folders, routing, data flow | `FRONTEND_ARCHITECTURE.md` |
| A specific component's spec | `COMPONENTS.md` |
| Motion/animation rules | `ANIMATION.md` |
| Breakpoint behavior | `RESPONSIVE.md` |
| Voice, tone, copy rules | `CONTENT.md` |
| What data is real vs illustrative | `MOCK_DATA.md` |
| Pre-ship checklist | `QA.md` |
| Build order | `DEVELOPMENT_ROADMAP.md` |
| Rules for coding agents in this repo | `VIBECODING_RULES.md` |
