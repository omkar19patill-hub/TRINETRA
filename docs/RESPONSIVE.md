# TRINETRA — Responsive Rules

## Principle

Do not merely shrink desktop UI. Preserve information hierarchy.

## Breakpoints

Use Tailwind's built-in breakpoints only — no custom breakpoints:

```text
(default)  mobile     < 640px
sm         —          ≥ 640px
md         tablet      ≥ 768px
lg         desktop       ≥ 1024px
```

Three tiers for QA purposes: **Mobile, Tablet, Desktop.** (This resolves an
earlier inconsistency where the QA checklist referenced tiers — "Laptop,"
"Wide desktop" — that the design docs never defined. Test against these
three only.)

## Desktop (`lg`+)

Full layout: hero's two-column split with `PipelineVisual` visible, 4-column
stat grid, 5-column pipeline stepper, side-by-side data-sources layout.

## Tablet (`md`)

Collapsible/hidden desktop nav pill replaced by hamburger drawer at this
tier and below. 2-column stat grid. Pipeline stepper may wrap to a shorter
row or 2×3 grid — no loss of any step.

## Mobile (default, `<640px`)

- Single column throughout.
- Drawer navigation (hamburger toggle).
- Hero: `PipelineVisual` hidden (`hidden lg:block`); headline and copy carry
  the section alone.
- Stat cards: 2-column grid.
- Pipeline stepper: single column, stacked.
- Product preview card: single column (risk/exposure cards stack above the
  budget slider).
- Full-width primary CTAs.

### Tables / dense data
Not applicable to the marketing site. When the dashboard phase introduces
tables, use horizontal scroll when column relationships matter, or cards
only when the dataset survives that without losing relationships.

### Charts / SVG diagrams
Must fit their container, retain readable labels, and avoid tiny legends.
The hero's `PipelineVisual` and the `DataSources` beam diagram are both
`hidden` below `lg` rather than shrunk to illegibility — this is a
deliberate choice, not a gap.

## Touch

Do not depend on hover. All interactive controls, including the budget
slider's handle, must be comfortable to operate via touch (≥44px target).
