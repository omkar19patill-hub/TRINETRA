# CLAUDE.md

Context Claude Code should have at the start of every session in this repo.
This file is deliberately short — it points to the real documentation rather
than repeating it, so it doesn't go stale.

## What TRINETRA Is

AI-powered continuous cyber risk quantification and investment optimization
platform. Built for SIH26105 (Smart India Hackathon 2026, Blockchain &
Cybersecurity theme). Core pipeline: CVE → Threat Intelligence → Risk →
Financial Risk (₹) → Investment Optimization → Security Action.

## Repo Layout

```
TRINETRA/
├── AGENTS.md              Backend AI-agent development rules — read before backend work
├── docs/                   Backend integration/optimization contracts (if present)
├── Backend/                 Unified FastAPI app — risk, financial_crq, monte_carlo,
│                              controls, optimization, decision, ml, ai, blockchain,
│                              orchestration, ingestion/integrations/validation/normalization
├── Frontend/
│   └── docs/                 Frontend documentation pack — FRONTEND_CONTEXT.md is the
│                               entry point; DESIGN.md, COMPONENTS.md, FRONTEND_ARCHITECTURE.md,
│                               VIBECODING_RULES.md, etc. live here
└── Assets/                  Logo, symbol, architecture diagrams
```

## Read Before Working — In This Order

1. **This file.**
2. **`AGENTS.md`** — before any backend change.
3. **`Frontend/docs/FRONTEND_CONTEXT.md`** — before any frontend change. It links to
   everything else; `VIBECODING_RULES.md`'s "Required docs" section tells you which
   other doc to read for which kind of task. Don't load the whole doc set for a
   small task — read what's relevant, per that section.
4. **Inspect the actual current code** before trusting any doc's description of it.
   Docs and code have drifted from each other before in this project — when they
   disagree, say so, don't silently pick one.

## Rules That Apply Everywhere

- Inspect existing code/components/schemas before creating new ones. Prefer
  extending over duplicating.
- Make the smallest change that correctly does the job. Don't refactor
  unrelated code, rename files without reason, or make an architectural
  change without flagging it first.
- Never invent an API endpoint, request/response field, or schema that isn't
  actually present in the code. If something needed doesn't exist yet, say
  so — don't fill the gap with a plausible guess.
- Never weaken a check to make it pass (e.g. turning off a TypeScript/lint
  rule instead of fixing what it caught). This has happened before in this
  repo — fix the real cause.
- The frontend's visual system (near-black surfaces, Inter, `#3355FF`
  accent, the validated section structure) is locked. Don't redesign it or
  introduce a different visual direction without explicit approval.
- Don't commit or push unless explicitly told to.
- Don't claim a build/test/integration passed without actually running it.

## Known Open Question — Verify, Don't Assume Either Way

`Backend/decision/` and `Backend/optimization/` may still be two parallel,
overlapping systems (one older with hardcoded benchmark seed data, one newer
matching `OPTIMIZATION_CONTRACT.md`). This may or may not be resolved by the
time you're reading this — check current imports/routes/orchestration wiring
yourself rather than trusting this note or a prior session's summary.

## Frontend Git Hygiene

The real frontend implementation has been lost from git history once before
(an early commit included `node_modules/` due to an incomplete
`.gitignore`, and got wholesale-deleted during cleanup). Before committing
frontend work, confirm `Frontend/.gitignore` actually excludes
`node_modules/` and `dist/`. Commit real work promptly — don't let
substantial uncommitted work sit only in the working directory.

## Commands

Frontend (`Frontend/`): `npm run dev`, `npm run build` — confirm exact
script names in `Frontend/package.json`, they weren't re-verified when this
file was written.

Backend (`Backend/`): tests exist as `pytest`-style files under
`Backend/tests/`; confirm exact run command and app entry point in
`Backend/README.md` — both have changed as the backend was consolidated
from three services into one.
