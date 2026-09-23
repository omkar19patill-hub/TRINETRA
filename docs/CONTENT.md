# TRINETRA — Content & Naming

## Tone

Concise, confident, technical, factual, decision-oriented.

## Product Vocabulary

| Term | Meaning |
|---|---|
| Threat | Potential harmful event/activity |
| Vulnerability | Weakness that can be exploited |
| Asset | System/resource being protected |
| Risk | Quantified exposure from threat/vulnerability/asset conditions |
| Financial Risk | Estimated monetary consequence |
| Investment | Security spending/control allocation |
| Mitigation | Action that reduces exposure |
| Simulation | What-if analysis |
| Priority | Relative urgency/order of action |

Use these terms consistently — don't introduce synonyms for the same
concept across sections.

## CTA Language

Prefer:
```text
Explore the platform
How it works
Run a simulation
View details
```

Avoid:
```text
Click Here
Learn More!!!
Fix Now!!!
Secure Everything
```

## Numbers

Bad: `72`
Better: `72 /100 — Overall Risk`

Bad: `₹18.4 Cr`
Better: `₹18.4 Cr — Estimated Financial Exposure`

Every real statistic carries its source in small type beneath it. Every
illustrative/demo value carries a "demo data" label — see `MOCK_DATA.md` for
which is which.

## Error Copy (dashboard phase — not used in marketing site)

State what happened, then what to do:

```text
Risk data could not be loaded.
Try again or check the data source connection.
```

## Marketing vs. Product Voice

Marketing (this phase):
> See risk before it strikes.

Product (dashboard phase, future):
> Estimated Financial Exposure

Do not use hype-heavy marketing language inside analytical UI, and don't let
dashboard-style bare labels leak into marketing copy — marketing sections
get a full sentence of context, dashboard components get a compact label.
