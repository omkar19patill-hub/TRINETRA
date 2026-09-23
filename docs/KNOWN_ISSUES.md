# TRINETRA — Known Issues

Pre-existing issues confirmed in the current codebase. Each entry records the
defect, how it is triggered, the risk, and a safe workaround. Fixing these is
tracked separately — this file is documentation only.

---

## 1. Test suite silently overwrites tracked model artifact and training data

**Status:** Open — not fixed.

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

### Safe workaround

Until this is fixed, do not run the backend test suite directly against the real
working tree. Run it against an isolated export instead, for example:

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

This is a pre-existing defect, not introduced by recent changes. Fixing it
would mean threading the target paths through `train_and_save_model()` — a
production-code change that should be reviewed on its own.
