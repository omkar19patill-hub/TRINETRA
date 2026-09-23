# TRINETRA — Frontend QA

## Build

- [ ] TypeScript passes
- [ ] Production build passes
- [ ] Lint passes
- [ ] No console errors
- [ ] No broken anchor links
- [ ] No missing assets

## Visual

- [ ] Typography follows `DESIGN.md`
- [ ] Spacing uses approved tokens only
- [ ] Semantic color tokens used — no raw hex in component files
- [ ] Borders and radius consistent with `DESIGN.md`
- [ ] No random gradients beyond the validated CTA headline treatment
- [ ] No excessive glow
- [ ] Matches the validated prototype's visual direction (not a redesign)

## Components

For every interactive component:
- [ ] Default, hover, focus-visible, active, disabled states all defined

For data-driven components (`ProblemStats`, `BudgetSlider` output):
- [ ] Long content / overflow handled
- [ ] Real vs. demo data clearly distinguished (see `MOCK_DATA.md`)

## Accessibility

- [ ] Keyboard navigation across the whole page, including the anchor nav
- [ ] Visible focus on every interactive element
- [ ] Accessible names on icon-only controls (hamburger toggle, etc.)
- [ ] Budget slider has a label and `aria-label`
- [ ] No color-only meaning (risk levels always paired with text)
- [ ] WCAG 2.2 AA contrast checks pass
- [ ] `prefers-reduced-motion` respected

## Responsive

Test against the three tiers defined in `RESPONSIVE.md`:
- [ ] Mobile (< 640px)
- [ ] Tablet (768–1023px)
- [ ] Desktop (≥ 1024px)

Check per tier:
- [ ] Navbar (drawer vs. pill nav)
- [ ] Hero (`PipelineVisual` hidden below `lg`)
- [ ] Stat grid column count
- [ ] Pipeline stepper layout
- [ ] Product preview card stacking
- [ ] Touch target size on the budget slider

## UX

- [ ] The pipeline is understandable within seconds of viewing the hero
- [ ] Every real statistic shows its source
- [ ] Demo data is clearly labeled
- [ ] No sensational language (see `CONTENT.md`)
- [ ] No dead anchor links

## Performance

- [ ] Images optimized
- [ ] No unnecessary dependencies (no animation library — see `ANIMATION.md`)
- [ ] Font loading doesn't cause major layout shift
