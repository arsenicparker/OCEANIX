# OCEANIX: AI-Based Marine Intelligence

**Fishing-Zone Suitability Prediction and Map-Based Decision Support**  
*A defensible, transparent, and reproducible data-to-application engineering workflow.*

---

## 1. Overview
OCEANIX is an educational decision-support prototype that uses marine environmental observations and fishery data to estimate fishing-zone suitability. The project demonstrates an end-to-end engineering workflow:
1. **Data Acquisition & Audit**: Inspect provenance, coverage, quality, and label validity before committing to machine learning.
2. **Deterministic Processing**: Parse coordinates, align environmental variables across space and time, and prevent data leakage.
3. **Machine Learning Pipeline**: Compare an interpretable primary estimator (`RandomForest`) against an honest baseline (`DummyEstimator`) on held-out temporal/spatial splits.
4. **Validated API**: Expose predictions and model metadata via FastAPI with strict Pydantic schemas.
5. **Interactive Interface**: Render estimates and historical advisories on a responsive Leaflet map with explicit attribution and limitations.

> **Responsible Use Disclaimer**: OCEANIX is an educational prototype and decision-support tool. It is **not** official marine advice, a navigation system, or an operational fishing guarantee. A "high suitability" score does not guarantee catch or safety, and "low suitability" does not imply fish absence.

---

## 2. Repository Layout
```
OCEANIX/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ data/
│   ├─ raw/            # Source files (immutable)
│   ├─ interim/        # Cleaned / joined intermediate data
│   └─ processed/      # Final model-ready dataset
├─ docs/
│   ├─ dataset_audit.md
│   ├─ data_sources.md
│   ├─ project_scope.md
│   ├─ ml_plan.md
│   ├─ ml_results.md
│   └─ limitations.md
├─ notebooks/          # Exploratory analysis
├─ src/oceanix/
│   ├─ data/           # Download, validation, alignment routines
│   ├─ features/       # Feature engineering & preprocessing pipeline
│   ├─ modeling/       # Model training, evaluation, artifact export
│   └─ api/            # FastAPI application & Pydantic schemas
├─ frontend/           # Responsive HTML/CSS/JS + Leaflet map
├─ models/             # Exported pipeline & metadata (.joblib git-ignored)
└─ tests/              # Automated unit and smoke tests
    ├─ test_data_checks.py
    ├─ test_model_smoke.py
    └─ test_api.py
```

---

## 3. Quick Start & Setup

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/arsenicparker/OCEANIX.git
cd OCEANIX

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 4. Current Status
- [x] Repository structure and initial configuration established.
- [x] Milestone M1: Data Audit & Source Verification (Completed).
- [x] Milestone M2: Dataset Preparation & Preprocessing (Completed).
- [x] Milestone M3: Machine Learning Pipeline & Training (Completed).
- [x] Milestone M4: Model Evaluation & Limitations Reporting (Completed).
- [x] Milestone M5: FastAPI Service & Schemas (Completed).
- [x] Milestone M6: Frontend & Interactive Leaflet Map (Completed).
- [x] Design Diagram added.
- [x] Milestone M7: Integration, QA & End-to-End Testing (Completed).
- [x] Milestone M8: Final Deliverables & Demonstration (Completed).

---

---

## 5. Running the Application Locally
```bash
# Start FastAPI and web application
python -m uvicorn oceanix.api.main:app --host 127.0.0.1 --port 8000 --reload

# Open web prototype in browser
# http://127.0.0.1:8000/
# API Documentation (Swagger UI)
# http://127.0.0.1:8000/docs
```

---

## 6. Full reproducibility guide
To reproduce the entire workflow from a clean clone:
1. **Clone the repository**
   ```bash
   git clone https://github.com/arsenicparker/OCEANIX.git
   cd OCEANIX
   ```
2. **Create a virtual environment & install dependencies**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Run the test suite** to verify the data‑audit, model, API and UI layers:
   ```bash
   pytest -q
   ```
4. **Start the FastAPI service** (as shown above) and open the UI at `http://127.0.0.1:8000/`.
5. **Optional**: Review the architecture diagram – see `docs/design_diagram.md`.

---

## 7. Architecture diagram
A high‑level flow of data from raw sources to the interactive UI is visualised in [design_diagram.md](docs/design_diagram.md).



