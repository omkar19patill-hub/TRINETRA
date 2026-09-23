# AI Automation Agency Landing Page Template

## Mission
Create implementation-ready, token-driven UI guidance for AI Automation Agency Landing Page Template that is optimized for consistency, accessibility, and fast delivery across marketing site.

## Brand
- Product/brand: AI Automation Agency Landing Page Template
- URL: https://www.aura.build/templates/ai-automation-84
- Audience: buyers, teams, and decision-makers
- Product surface: marketing site

## Style Foundations
- Visual style: structured, tokenized, content-first
- Main font style: `font.family.primary=Inter`, `font.family.stack=Inter, sans-serif`, `font.size.base=14px`, `font.weight.base=400`, `font.lineHeight.base=20px`
- Typography scale: `font.size.xs=10px`, `font.size.sm=11px`, `font.size.md=12px`, `font.size.lg=14px`, `font.size.xl=16px`, `font.size.2xl=18px`, `font.size.3xl=24px`, `font.size.4xl=48px`
- Color palette: `color.text.primary=#a6a6a6`, `color.text.secondary=#fafafa`, `color.text.tertiary=#ffffff`, `color.text.inverse=#737373`, `color.surface.base=#000000`, `color.surface.muted=#050505`, `color.surface.raised=#262626`, `color.surface.strong=#171717`, `color.border.default=#333333`
- Spacing scale: `space.1=2px`, `space.2=4px`, `space.3=6px`, `space.4=8px`, `space.5=12px`, `space.6=16px`, `space.7=20px`, `space.8=24px`
- Radius/shadow/motion tokens: `radius.xs=4px`, `radius.sm=6px`, `radius.md=12px`, `radius.lg=16px`, `radius.xl=9999px` | `shadow.1=rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.24) 0px 5px 16px 0px, rgba(0, 0, 0, 0.18) 0px 1px 2px 0px, rgba(255, 255, 255, 0.1) 0px 1px 0px 0px inset`, `shadow.2=rgb(255, 255, 255) 0px 0px 0px 0px, rgba(255, 255, 255, 0.2) 0px 0px 0px 1px, rgba(0, 0, 0, 0.035) 0px 2.8px 2.2px 0px, rgba(0, 0, 0, 0.047) 0px 6.7px 5.3px 0px, rgba(0, 0, 0, 0.06) 0px 12.5px 10px 0px, rgba(0, 0, 0, 0.07) 0px 22.3px 17.9px 0px, rgba(0, 0, 0, 0.086) 0px 41.8px 33.4px 0px, rgba(0, 0, 0, 0.12) 0px 100px 80px 0px`, `shadow.3=rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0.05) 0px 1px 2px 0px`, `shadow.4=rgba(0, 0, 0, 0.05) 0px 1px 0px 0px, rgba(0, 0, 0, 0.1) 0px 4px 4px 0px, rgba(0, 0, 0, 0.15) 0px 10px 10px 0px, rgba(0, 0, 0, 0.1) 0px -1px 0px 0px inset` | `motion.duration.instant=150ms`, `motion.duration.fast=300ms`

## Accessibility
- Target: WCAG 2.2 AA
- Keyboard-first interactions required.
- Focus-visible rules required.
- Contrast constraints required.

## Writing Tone
Concise, confident, implementation-focused.

## Rules: Do
- Use semantic tokens, not raw hex values, in component guidance.
- Every component must define states for default, hover, focus-visible, active, disabled, loading, and error.
- Component behavior should specify responsive and edge-case handling.
- Interactive components must document keyboard, pointer, and touch behavior.
- Accessibility acceptance criteria must be testable in implementation.

## Rules: Don't
- Do not allow low-contrast text or hidden focus indicators.
- Do not introduce one-off spacing or typography exceptions.
- Do not use ambiguous labels or non-descriptive actions.
- Do not ship component guidance without explicit state rules.

## Guideline Authoring Workflow
1. Restate design intent in one sentence.
2. Define foundations and semantic tokens.
3. Define component anatomy, variants, interactions, and state behavior.
4. Add accessibility acceptance criteria with pass/fail checks.
5. Add anti-patterns, migration notes, and edge-case handling.
6. End with a QA checklist.

## Required Output Structure
- Context and goals.
- Design tokens and foundations.
- Component-level rules (anatomy, variants, states, responsive behavior).
- Accessibility requirements and testable acceptance criteria.
- Content and tone standards with examples.
- Anti-patterns and prohibited implementations.
- QA checklist.

## Component Rule Expectations
- Include keyboard, pointer, and touch behavior.
- Include spacing and typography token requirements.
- Include long-content, overflow, and empty-state handling.
- Include known page component density: links (67), buttons (52), lists (6), navigation (3), inputs (1).

- Extraction diagnostics: Audience and product surface inference confidence is low; verify generated brand context.

## Quality Gates
- Every non-negotiable rule must use "must".
- Every recommendation should use "should".
- Every accessibility rule must be testable in implementation.
- Teams should prefer system consistency over local visual exceptions.
