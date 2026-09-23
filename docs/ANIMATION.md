# TRINETRA — Motion & Interaction

## Philosophy

Motion communicates hierarchy, state change, navigation, or feedback. It is
not the main attraction. Spend boldness in one place — the hero's pipeline
visualization is that place. Everything else stays quiet.

## Timing

```text
150ms — instant (hover, controls)
300ms — fast (card/section reveal)
```

## Validated Motion Inventory

These four effects are already validated in the prototype. Port them
directly — do not invent new ones without reason.

| Effect | Used for | Notes |
|---|---|---|
| `float` | Node cards in Hero/DataSources | Subtle `translateY`, staggered delays, 6s ease-in-out loop |
| `dash-flow` | Beam/path lines | `stroke-dasharray` + `stroke-dashoffset` animation, 18s linear loop |
| `packet-pulse` | Small status dots (e.g. the "live" indicator badge) | Scale + opacity pulse, 2.4s |
| `gradient-x` | CTA headline text | Animated gradient position, 6s ease loop |

**Implementation gotcha (already hit once — don't repeat it):** a CSS
`transform` animation applied to an SVG `<g>` that also carries a `transform`
attribute can override that attribute entirely, collapsing its position.
Always wrap: outer `<g transform="translate(x,y)">` for position, inner
`<g class="animate-float">` for the animation. Never both on the same
element.

## Preferred Patterns

### Hover
Subtle border change, subtle surface change, 1px lift where useful, opacity
adjustment.

### Page reveal
One orchestrated moment on load — not a fade-up on every section. Use the
`useInView` hook (`src/hooks/useInView.ts`, plain `IntersectionObserver`,
no library) if a scroll-triggered reveal is used at all, and use it
sparingly.

### CTA button
The conic-gradient spinning border reveal on hover — reserved for the
primary CTA button variant only (see `COMPONENTS.md`).

### Loading
Prefer skeletons for page-level loading (dashboard phase). For the one
interactive element in this phase (the budget slider), updates are
synchronous and need no loading state.

## Avoid

Infinite decorative animation beyond the validated inventory above,
aggressive glitch effects, excessive neon glow, constant pulsing beyond the
one status dot, large parallax, animation on every card, interaction-blocking
animation.

## Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}
```

Apply this globally, once, in `styles/globals.css`.

## Scroll

`html { scroll-behavior: smooth }` powers the anchor navigation. Each
section needs `scroll-margin-top` matching the fixed navbar's height so
anchored sections don't render underneath it.
