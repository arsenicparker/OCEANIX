# OCEANIX Implementation Plan

*Based strictly on the Project Blueprint (Version 1.0, 13 October 2026). No features have been added or removed.*

---

## 1. Overview
This plan translates the blueprint into concrete, time‑boxed work items. It follows the **14‑working‑day schedule** and the **repository structure** described in Section 15 of the blueprint. All deliverables are listed with clear exit criteria.

---

## 2. Repository Layout (Section 15)
```
OCEANIX/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ data/
│   ├─ raw/            # source files (immutable)
│   ├─ interim/        # cleaned/joined temporary data
│   └─ processed/      # final model‑ready table
├─ docs/
│   ├─ dataset_audit.md
│   ├─ data_sources.md
│   ├─ project_scope.md
│   ├─ ml_plan.md
│   ├─ ml_results.md
│   └─ limitations.md
├─ notebooks/          # optional exploratory notebooks
├─ src/oceanix/
│   ├─ data/           # download / validation / alignment
│   ├─ features/       # preprocessing pipeline
│   ├─ modeling/       # training / evaluation / export
│   └─ api/            # FastAPI app & Pydantic schemas
├─ frontend/           # responsive HTML/CSS/JS + Leaflet map
├─ models/             # saved pipeline + metadata (git‑ignored)
└─ tests/
    ├─ test_data_checks.py
    ├─ test_model_smoke.py
    └─ test_api.py
```

---

## 3. Detailed Work Breakdown (aligned to Blueprint Sections)

### Day 1‑2 – Data Audit (Milestone M1)
1. **Create audit notebook/script** (`src/oceanix/data/audit.py`).
2. **Download candidate datasets** (INCOIS PFZ & environmental products *or* NOAA/NCEI 0306675) into `data/raw/`.
3. **Run the checklist** (Section 7 tables) and produce `docs/dataset_audit.md` covering:
   - Provenance, time coverage, geography, schema, target validity, feature‑target match, sample quality, licensing, repeatability.
4. **Decision** – Record GO / CONDITIONAL‑GO / NO‑GO in the audit file.
5. **Commit** audit script and markdown.

### Day 3‑4 – Dataset Preparation (Milestone M2)
1. Implement deterministic preprocessing (`src/oceanix/data/prepare.py`) that:
   - Reads raw files (CSV/Excel/NetCDF) without modifying originals.
   - Converts DMS to decimal degrees, validates ranges.
   - Parses dates with explicit formats, preserves time‑zone.
   - Joins environmental variables to target records using documented spatial/temporal tolerance.
   - Generates `data/interim/cleaned_<source>.csv` and logs row‑count changes.
2. Produce `docs/data_sources.md` (sources, URLs, checksums) and `docs/project_scope.md` (chosen route – A or B).
3. Verify that the resulting table meets all audit checklist items; update audit if needed.
4. Add unit tests (`tests/test_data_checks.py`) for schema, missingness, coordinate validity.

### Day 5‑6 – Machine‑Learning (Milestone M3)
1. Define the **target** based on the audit outcome (Section 8).
2. Create a scikit‑learn `Pipeline` (`src/oceanix/modeling/pipeline.py`) that includes:
   - `ColumnTransformer` for numeric imputation / optional missing‑indicator flags.
   - Baseline estimator (`DummyClassifier`/`DummyRegressor`).
   - Primary model (`RandomForestClassifier` or `RandomForestRegressor`).
3. Implement split logic respecting temporal/spatial groups (Section 10). Use a frozen test set.
4. Train baseline → train primary model → compute metrics (Section 11 tables).
5. Save the fitted pipeline and metadata to `models/pipeline.joblib` and a corresponding `ml_results.md` report.
6. Add `tests/test_model_smoke.py` to load the artifact and run a single inference.

### Day 7 – Evaluation & Reporting (Milestone M4)
1. Generate metric tables (confusion matrix, precision/recall/F1 *or* MAE/RMSE/R²) and plots.
2. Write `docs/ml_results.md` containing:
   - Dataset split description.
   - Baseline vs model metrics.
   - Feature‑importance (permutation or native) visualisation.
   - Explicit limitation statements (Section 11).
3. Review against the **minimum reported metrics** checklist; iterate if needed.

### Day 8‑9 – API Development (Milestone M5)
1. Build FastAPI app (`src/oceanix/api/main.py`) with endpoints:
   - `GET /health`
   - `GET /model-info`
   - `POST /predict`
2. Define request/response schemas using Pydantic (Section 13). Enforce validation, 4xx errors, and CORS limited to `http://localhost:<frontend‑port>`.
3. Load the saved pipeline at startup (singleton). No retraining per request.
4. Write `tests/test_api.py` covering success and error cases.
5. Verify with `uvicorn src.oceanix.api.main:app --reload`.

### Day 10‑11 – Front‑End & Map (Milestone M6)
1. Create a responsive HTML/CSS/JS UI under `frontend/`:
   - Home/overview page.
   - Input form (date picker, lat/lon fields) that matches the API schema.
   - Result display with prediction value, target description, model version, and disclaimer.
   - Leaflet map that:
     * Shows historical advisory points (if available) with distinct marker.
     * Shows model prediction marker (different colour/legend).
     * Includes OSM attribution.
2. Style with a premium, glassmorphism‑inspired palette (dark mode, modern typography – e.g., Google Font *Inter*). Add subtle hover animations.
3. Connect UI to API via `fetch` calls; display loading spinner and clear error messages.
4. Add a “About / Limitations” modal containing the disclaimer from Section 11.
5. Manually test on desktop and mobile viewport sizes.

### Day 12‑13 – Integration, QA & Documentation (Milestone M7)
1. Run the full **end‑to‑end** flow:
   - Data audit → preprocessing → model training → API → UI → map.
2. Execute the entire test suite (`pytest -q`). All must pass.
3. Update `README.md` with:
   - Project description.
   - Setup instructions (virtual env, `pip install -r requirements.txt`).
   - Step‑by‑step run guide (data audit → `uvicorn` → open UI).
   - Links to generated docs (`docs/`).
4. Ensure reproducibility: record Python version, package versions (pin in `requirements.txt`), and random seeds.
5. Commit all code, docs, and non‑large data artefacts.

### Day 14 – Final Deliverables & Demo (Milestone M8)
1. Compile the final **project report** (single PDF or Markdown) containing:
   - Executive summary.
   - Dataset audit & source list.
   - ML methodology & results.
   - API specification.
   - UI screenshots (including map legend).
   - Acceptance checklist evidence.
2. Prepare a **demo script** (≈4 min) following the flow in Section 20.
3. Verify that a clean clone of the repo can be set up from the README and reproduced end‑to‑end.
4. Archive the demo video/screenshots in the `docs/` folder.

---

## 4. Acceptance Checklist (Section 19) – Mapping to Deliverables
| Requirement | Deliverable | Verification |
|---|---|---|
| Source & target verified | `docs/dataset_audit.md` + `docs/project_scope.md` | Audit GO decision documented |
| No fabricated data/results | Raw files unchanged, audit logs, reproducible pipeline | Git diff shows only code changes |
| Model evaluated on unseen data | `docs/ml_results.md` with held‑out metrics | Test set defined before training |
| Beats / compares to baseline | Metric table in `ml_results.md` | Baseline vs model numbers shown |
| API supports correct schema | `src/oceanix/api/main.py` + `tests/test_api.py` | All tests pass |
| UI renders correct semantics | `frontend/` with map legend, disclaimer | Manual UI test + screenshots |
| Limitations visible | Disclaimer in UI and `docs/limitations.md` | Present in both places |
| Reproducible from README | `README.md` + CI‑style test run | Clean clone reproduces end‑to‑end |

---

## 5. Risk Mitigation (referencing Section 18)
| Risk | Mitigation in Plan |
|---|---|
| Data source inaccessible | Time‑box audit; prepare fallback NOAA/NCEI route; document decision before ML.
| No defensible target | Audit explicitly requires target validity; if absent, shift to a transparent environmental index (Plan C).
| Data leakage | Split created **before** any preprocessing; pipeline trained only on training split.
| Weak model performance | Baseline comparison required; if model does not improve, report honestly and consider index.
| Map authority perception | Distinct markers, clear legends, pervasive disclaimer, UI‑level warning.
| Dependency issues | Minimal pinned `requirements.txt`; test on fresh environment.

---

## 6. Next Steps
- **Create the repository** with the layout above.
- **Add `README.md`** placeholder and commit.
- **Proceed to Day 1** tasks (data download & audit).

*All subsequent work must reference the sections and tables of the original blueprint; no additional features shall be introduced without explicit blueprint amendment.*

---

*Implementation plan saved to `IMPLEMENTATION_PLAN.md` in the project root.*
