# Final Project Report – OCEANIX

## Executive Summary
OCEANIX is an educational decision‑support prototype that predicts fishing‑zone suitability for skipjack tuna in the Western Indian Ocean.  The workflow is fully reproducible, from raw data audit through a scikit‑learn pipeline, a FastAPI service, and an interactive Leaflet UI.

## 1. Data Audit & Sources
- **INCOIS Karnataka PFZ advisory** – operational points, parsed and displayed on the map (no ML).  
- **NOAA/NCEI 0306675** – oceanographic variables used as features.  
- All sources are catalogued in `docs/dataset_audit.md` and `docs/data_sources.md`.

## 2. Dataset Preparation
- Deterministic preprocessing (`src/oceanix/data/prepare.py`) cleans, converts coordinates, merges variables, and writes `data/interim/cleaned_*.csv`.
- Unit tests (`tests/test_data_checks.py`) verify schema, missingness, and coordinate validity.

## 3. Machine‑Learning Pipeline
- Scikit‑learn `Pipeline` (`src/oceanix/modeling/pipeline.py`) with:
  - ColumnTransformer → numeric imputation
  - `RandomForestRegressor` (primary) vs `DummyRegressor` (baseline)
- Temporal/spatial split prevents leakage.  
- Metrics (MAE, RMSE, R²) stored in `docs/ml_results.md`.
- Serialized artifact: `models/pipeline.joblib` + `models/model_metadata.json`.

## 4. FastAPI Service (`src/oceanix/api/main.py`)
- Endpoints: `/health`, `/model-info`, `/predict`, `/advisories/karnataka`.
- Robust startup loading, CORS for local dev, and Pydantic request/response schemas.
- Full test suite (`tests/test_api.py`) ensures correct behaviour.

## 5. Front‑End UI (`frontend/`)
- Single‑page app with Leaflet map, input form, prediction badge, and advisory overlay.
- Responsive glassmorphism styling, dark‑mode palette, and disclaimer modal.
- Communicates with the API via `fetch` calls.

## 6. Continuous Integration
- GitHub Actions workflow `.github/workflows/ci.yml` runs the test suite on Windows on every push.

## 7. Containerised Deployment
- **Dockerfile** builds a minimal image (`python:3.12‑slim`) installing the requirements and exposing port 8000.
- **docker‑compose.yml** provides a one‑line `docker compose up` to launch the service.

## 8. Release
- Tagged as **v1.0.0** and pushed to GitHub.
- All artefacts (code, docs, CI, Docker) are present in the repository.

## 9. Demonstration Script (see `docs/demo_script.md`)
- Clone repo → set up venv → run `pytest -q` → start API → open `http://127.0.0.1:8000/`.
- Verify map loads advisory points and prediction flow works.

---
**Limitations & Disclaimers** are reproduced throughout the UI, API docs, and `docs/limitations.md`.

