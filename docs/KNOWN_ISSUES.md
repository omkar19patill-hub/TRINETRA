# TRINETRA — Known Issues

Pre-existing issues confirmed in the current codebase. Each entry records the
defect, how it is triggered, the risk, and a safe workaround. Fixing these is
tracked separately — this file is documentation only.

---

## 1. Test suite silently overwrites tracked model artifact and training data

**Status:** RESOLVED. See "Resolution" below. The description that follows records
the original defect for historical context.

### Bug

`train_and_save_model()` writes to hardcoded module-level paths and ignores any
injected or temporary path supplied by the caller:

- `Backend/ml/train.py:28` — `MODEL_PATH = BASE_DIR / "ml" / "model.joblib"`
- `Backend/ml/train.py:29` — `DATASET_PATH = DATA_DIR / "ml_training.csv"`
- `Backend/ml/train.py:157` — `df.to_csv(DATASET_PATH, index=False)`
- `Backend/ml/train.py:214` — `joblib.dump(artifact, MODEL_PATH)`

`RiskCalibrationModel.__init__` accepts a `model_path`, but its fallback at
`Backend/ml/model.py:43-54` (`_load_or_train`) calls `train_and_save_model()`
with no arguments, so the injected path is discarded for writes.

### Trigger

Running the backend test suite directly inside the real `Backend/` directory.
Specifically `test_missing_model_file_fallback(tmp_path)` at
`Backend/tests/test_ml_component.py:173`: it passes a `tmp_path` so the artifact
is intentionally absent, which forces the fallback — and the fallback then
writes to the real repository paths rather than the temp directory.

### Risk

The test silently overwrites two tracked files:

- `Backend/ml/model.joblib`
- `Backend/data/ml_training.csv`

Confirmed reproducible: the artifact hash changed across consecutive runs, and
the rewritten artifact differed in size from the committed one (4374 -> 4358
bytes). A committed, reviewed model artifact can therefore be replaced by an
incidental retrain with no warning, and the change is easy to commit by
accident.

### Resolution

Fixed by making the training entry point accept its output locations instead of
always writing to module-level constants.

- `Backend/ml/train.py` — `train_and_save_model()` now takes optional
  `model_path` and `dataset_path` parameters. Both default to the existing
  `MODEL_PATH` / `DATASET_PATH` constants, so normal application behaviour is
  unchanged. The `to_csv` and `joblib.dump` calls write to the resolved targets.
- `Backend/ml/model.py` — `RiskCalibrationModel` accepts an optional
  `dataset_path`, and `_load_or_train()` now passes both paths into
  `train_and_save_model()`. When only a custom `model_path` is supplied, the
  dataset is written alongside it (`_resolve_dataset_path()`), so a caller
  pointing at a temporary directory never writes into the repository. When the
  defaults are in use, `None` is passed and `train.py` applies its own defaults.

Three regression tests were added in `Backend/tests/test_ml_component.py`:

- `test_fallback_training_does_not_touch_repository_artifacts` — asserts the
  injected temp paths receive both artifacts and that the SHA-256 of the tracked
  `ml/model.joblib` and `data/ml_training.csv` are unchanged.
- `test_fallback_training_accepts_explicit_dataset_path` — asserts an explicit
  `dataset_path` is honoured.
- `test_default_paths_still_resolve_to_repository_artifacts` — asserts default
  construction still resolves to the repository artifact (no behaviour change).

All three fail against the pre-fix code and pass after it. Verified by running
the full suite directly inside `Backend/` (178 passed) and confirming both
tracked files were byte-identical before and after, with a clean `git status`.

### Safe workaround (no longer required)

Retained for reference. Before the fix, the rule was: do not run the backend test
suite directly against the real working tree; run it against an isolated export
instead, for example:

    git archive HEAD | tar -x -C <isolated-dir>
    cd <isolated-dir>/Backend && python -m pytest tests/ -q

The git-archive export path does **not** trigger this bug: `BASE_DIR` is derived
from `Path(__file__).resolve().parent.parent` (`Backend/ml/train.py:26`), so it
resolves relative to the location of the imported `train` module rather than the
current working directory. When the suite runs against an export, the imported
module is the export's copy, so `MODEL_PATH` and `DATASET_PATH` resolve to
`<isolated-dir>/Backend/ml/model.joblib` and
`<isolated-dir>/Backend/data/ml_training.csv`, and the real repository is never
written to. This was verified by importing `ml.train` from an export and
printing the resolved constants, which pointed inside the export directory.
The protection depends on the module being imported *from* the export — if
`sys.path` or `PYTHONPATH` still points at the real `Backend/`, writes go to the
real repository regardless of the current working directory.

If the suite has already been run in place, verify before committing:

    git status --short
    git diff --stat

and restore any incidental changes with
`git restore Backend/ml/model.joblib Backend/data/ml_training.csv`.

### Scope note

This was a pre-existing defect, not introduced by recent changes. It has since
been fixed by threading the target paths through `train_and_save_model()`, as
described under "Resolution".

---

## 2. Stale control-name map in `_to_ctrl_id()` (latent, never confirmed live)

**Status:** RESOLVED by removal. Recorded here because the investigation findings
are worth keeping, including the part that did **not** hold up.

### What was found

`_to_ctrl_id()` in `Backend/orchestration/service.py` translated control names to
control IDs via a hardcoded 20-entry lowercase map, falling back to
`item.strip().upper()` on a miss.

Four benchmark control names were renamed in commit `f9f0fea`
("data(decision): revise benchmark control economics"), but the map kept the
pre-rename keys:

| Name after `f9f0fea` (`decision/store.py`) | Map key (stale) |
|---|---|
| `Managed 24/7 SIEM & SOC Operations` | `siem & 24/7 soc triage` |
| `Continuous Phishing Simulation & Training` | `security awareness & phishing simulation` |
| `Zero Trust Network Access (ZTNA)` | `zero trust network architecture` |
| `Database Field-Level Encryption` | `database & field-level encryption` |

The staleness was verified by direct string comparison. Those four names would
have missed the map and fallen through to `.upper()`.

### Impact: latent, not reproducible

An initial assessment suggested this could produce false
`controls_added` / `controls_removed` results from `POST /reoptimize`.
**That was not confirmed, and attempts to reproduce it failed.**

The identical benchmark-baseline request was run against pre-fix and post-fix
code and returned the same delta in both cases:

```text
pre-fix   added: ['CTRL-TRAIN', 'CTRL-WAF']   removed: ['CTRL-EDR', 'CTRL-BACKUP']
post-fix  added: ['CTRL-TRAIN', 'CTRL-WAF']   removed: ['CTRL-EDR', 'CTRL-BACKUP']
```

The reason: the balanced-ROI benchmark portfolio only ever selects
CTRL-MFA / CTRL-PATCH / CTRL-EDR / CTRL-BACKUP / CTRL-PAM, all of which were
still mapped correctly. The four stale-named controls are lower ROI and are not
selected within the stored benchmark budgets (1,800,000 and 2,500,000). The
baseline portfolio is built from the stored optimization's own budget rather
than the request's `budget_limit`, so a larger request budget does not widen it.

Conclusion: the stale map was real, but **latent and unreachable** through the
current API surface with current benchmark data. It was not observed to produce
incorrect output.

### Resolution

Resolved as a side effect of the control-ID consistency change:
`decision/alternatives.py` now returns control IDs rather than names, so both
sides of the portfolio comparison use the same convention and no translation is
needed. `_to_ctrl_id()` was deleted rather than repaired.

This removes the latent hazard and the maintenance burden of a name map that had
already drifted once. It is recorded as a contract improvement, not as the fix
for a live defect.

### Scope note

Pre-existing on `main`. Surfaced during the API-contract investigation.

---

## 3. TypeScript strict mode is not enabled project-wide

**Status:** Open — **deliberate deferral, not an oversight.**

### What was found

No `"strict": true` appears in any frontend TypeScript configuration. Verified
across `Frontend/tsconfig.json`, `Frontend/tsconfig.app.json`,
`Frontend/tsconfig.node.json` and `Frontend/.oxlintrc.json`.

This contradicts two documents that assume strictness is already on:

- `VIBECODING_RULES.md` — "Preserve TypeScript strictness. Avoid `any`."
- `FRONTEND_ARCHITECTURE.md` §8 — "Avoid `any`."

### Risk

Without `strict`, `strictNullChecks` is off. A value that is `undefined` or
`null` at runtime — for example an optional field absent from a backend response
— will not be flagged at compile time. That risk grows as the frontend starts
consuming real API data rather than local mock modules.

### Why it is deferred

Enabling `strict` is likely to surface errors across the existing 26 source
files. Fixing those is a separate piece of work with its own review, and folding
it into a feature phase would mix unrelated changes in one diff.

It was explicitly deferred when the Phase 1 API client was built, with the
decision recorded here so it is not lost.

### Mitigation in the meantime

All Phase 1 API-layer code (`src/lib/apiClient.ts`, `src/config/env.ts`,
`src/types/api.ts`) was written to be strict-compatible: no `any`, `unknown`
plus narrowing at the JSON boundary, and explicit optional/nullable members on
response types. Turning `strict` on later should not require rewriting it.

### Planned resolution

Enable `strict` and fix the resulting errors as a standalone task **before**
Phase 2 dashboard screens are built, so new screens are written against strict
typing from the start rather than retrofitted.
