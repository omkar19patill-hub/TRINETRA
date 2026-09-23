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
