# TRINETRA — Frontend Design System

**Status: Final.** All tokens below are locked. Components must consume these
semantic tokens — never a raw hex value in a component file.

## 1. Design Intent

TRINETRA feels like a premium cyber-risk intelligence product: dark,
restrained, precise, typography-led, and information-dense without visual
noise. Structured, tokenized, content-first — validated against the
prototype referenced in `FRONTEND_CONTEXT.md`.

## 2. Typography

```css
font-family: Inter, sans-serif;
```

One typeface family, used throughout — no second display font. Hierarchy
comes from weight, size, and spacing, not a different font.

Base: 14px / weight 400 / line-height 20px.

```text
xs   10px
sm   11px
md   12px
lg   14px
xl   16px
2xl  18px
3xl  24px
4xl  48px
```

Marketing headings may exceed this scale (the validated hero headline runs
~54–60px) as a documented product-level exception — not a free-for-all.

## 3. Core Semantic Tokens

```text
surface.base      #000000
surface.muted     #050505
surface.strong    #171717
surface.raised    #262626

text.primary      #a6a6a6   (muted / secondary copy — see note below)
text.secondary    #fafafa   (high-emphasis copy)
text.tertiary     #ffffff   (headlines, maximum emphasis)
text.inverse      #737373   (reserved — no light surface exists yet; do not use until one does)

border.default    #333333
```

> **Naming note:** `text.primary` is intentionally the *lowest*-contrast of
> the three main text tokens, despite the name. Apply tokens by the contrast
> the content needs, not by literal name: use `text.tertiary`/`text.secondary`
> for headlines and important copy, `text.primary` for de-emphasized/muted
> text. This inversion is known and accepted, not a bug to "fix" by renaming
> mid-project.

### TRINETRA accent — FINAL

```text
accent.primary    #3355FF
accent.soft       #7C93FF   (hover states, secondary emphasis, gradient text)
```

Sourced from the TRINETRA logo mark. This is not provisional.

### Severity accents — FINAL

```text
risk.critical     #EF4444
risk.high         #F97316
risk.medium       #EAB308
risk.low          #22C55E
```

These are the only colors that may indicate risk severity. Never pair a
severity color with an unrelated meaning (e.g. don't reuse `risk.high` as a
generic "warning" toast color).

## 4. Spacing Tokens

```text
2px  4px  6px  8px  12px  16px  20px  24px
```

Do not introduce arbitrary spacing without a documented reason.

## 5. Radius

```text
xs  4px
sm  6px
md  12px
lg  16px
xl  9999px
```

- 6px — controls (buttons, inputs, sliders)
- 12px — cards
- 16px — large surfaces / containers
- pill (9999px) — status chips, the floating nav pill

## 6. Borders & Elevation

Default border: `#333333`. Prefer borders and surface contrast over heavy
shadows. Elevation (subtle shadow) is reserved for dropdowns, popovers,
modals, and floating panels — not for every card. No glowing cards, no
constant neon effects.

## 7. Motion

```text
instant = 150ms
fast    = 300ms
```

- Hover / controls: 150ms
- Card reveal / section reveal: 300ms

Respect `prefers-reduced-motion` everywhere. See `ANIMATION.md` for the full
motion inventory validated in the prototype.

## 8. Layout

**Desktop:** content max-width 1200–1440px, consistent gutters.
**Marketing sections:** generous vertical rhythm (`py-24`/`py-32` scale),
left-aligned content blocks, centered only for the closing CTA.

## 9. Visual Hierarchy

1. Primary decision / headline
2. Key metric
3. Supporting context
4. Evidence / detail
5. Metadata (sources, timestamps)

Use size, weight, spacing, and surface contrast before color.

## 10. Cards

Clear hierarchy, subtle borders (`border.default`), consistent padding, no
excessive shadow, no decorative icons unless they aid recognition.

## 11. Buttons

- **Primary:** high contrast — `text.tertiary` background, `surface.base`
  text. The validated prototype's spinning conic-gradient reveal on hover is
  the one sanctioned "bold" motion moment for a button — do not add it
  anywhere else.
- **Secondary:** bordered, `text.secondary`, transparent background.
- **Ghost:** minimal, tertiary actions only.

All states (default/hover/focus-visible/active/disabled/loading) must be
explicit — see `COMPONENTS.md`.

## 12. Status

Always text plus visual cue — never color alone:

```text
CRITICAL   HIGH   MEDIUM   LOW   MONITORED   MITIGATED
```

## 13. Charts

Minimal grid lines, readable labels, accessible contrast, exact-value
tooltips, no 3D, no unnecessary gradients. Prefer ranked bars over pies.
(Applies to the future dashboard phase — the marketing site has no real
charts, only the illustrative loss/risk numbers in the product preview.)

## 14. Tables

Compact rows, subtle dividers, strong column labels, clear hover, consistent
numeric alignment. (Dashboard phase — not used in the marketing site.)

## 15. Forms

Every field: label, control, helper text where needed, validation state,
error message. Never placeholder text as the only label. The one form-like
control in the marketing site is the demo budget slider — it still needs a
visible label and an accessible name.

## 16. Responsive

Use the framework's (Tailwind's) responsive system rather than custom
breakpoints. See `RESPONSIVE.md`.

## 17. Accessibility

Target WCAG 2.2 AA. Must preserve visible focus, meet contrast requirements,
support keyboard navigation, provide accessible names, support reduced
motion.

## 18. Anti-Patterns

Do not: use random gradients everywhere, use generic green "hacker" styling,
use stock cyber imagery, put shields/locks on every card, default to
glassmorphism, overuse glow, create one-off font sizes or spacing, hide
focus, use ambiguous CTAs ("Click Here", "Learn More!!!").
