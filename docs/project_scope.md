# OCEANIX Project Scope & Scientific Boundaries

*Document Version 1.0 — Milestone M1 (Data Audit)*  
*Prepared strictly according to Project Blueprint Section 1, 4, 5, and 8.*

---

## 1. Chosen Route & Scope Definition

Following the mandatory dataset audit (`docs/dataset_audit.md`), OCEANIX implements a defensible, multi-tier marine intelligence prototype:

### Primary Route: Route B — Western Indian Ocean Skipjack Tuna ML Model
- **Study Domain**: Western Indian Ocean (WIO), bounding box [38.75°E–79.75°E, -14.75°S–14.75°N].
- **Prediction Target**: Skipjack tuna (*Katsuwonus pelamis*) catch biomass (in metric tons per monthly $0.5^\circ$ cell), as recorded by the Indian Ocean Tuna Commission (IOTC).
- **Environmental Predictors**: 12 physical and biogeochemical ocean parameters from Copernicus Marine Service reanalysis (SST, Salinity, Chlorophyll-a, Mixed Layer Depth, Dissolved Oxygen, Currents, SSH, etc.).
- **Model Task**: Supervised Regression (`RandomForestRegressor` vs. `DummyRegressor` baseline) predicting estimated catch biomass / suitability index.
- **Evaluation Protocol**: Chronological holdout split (Training: 2005–2015; Frozen Test Set: 2016–2019) to prevent temporal data leakage and verify generalization.

### Operational Overlay: Route A — INCOIS Coastal Advisory Visualizer
- **Study Domain**: Coastal Karnataka, India [73.48°E–74.52°E, 13.18°N–14.72°N].
- **Purpose**: Real-world demonstration of parsing operational Potential Fishing Zone (PFZ) advisories issued by INCOIS (Ministry of Earth Sciences, GoI), converting Degree-Minute-Second (DMS) coordinates to decimal degrees, and rendering them on Leaflet with coastal station bearings and depth profiles.
- **Scientific Limitation**: The INCOIS advisory is explicitly presented as an **operational reference layer**, **not** as the output of the machine learning model.

---

## 2. Terminology & Truth in Reporting

To adhere to the Blueprint's ethical guidelines (Section 5 & 18):

| Allowed Plain-Language Terminology | Prohibited Claims (Scientific Misrepresentation) |
|---|---|
| "Historical catch biomass estimate" | "Guaranteed catch location" |
| "Marine habitat suitability proxy" | "Real-time live fish count" |
| "Decision-support prototype" | "Operational navigation system" |
| "Western Indian Ocean Skipjack tuna model" | "Model validated for Karnataka coastal species" |
| "Historical INCOIS advisory points" | "Live INCOIS satellite telemetry" |

---

## 3. Assumptions & Non-Goals

### Assumptions Verified
- Environmental variables (SST, Chlorophyll-a, MLD, etc.) correlate with pelagic fish aggregation but do not directly measure fish presence or fleet economics.
- The prototype operates on locally bundled, frozen historical datasets to ensure 100% scientific reproducibility.

### Explicit Non-Goals (Out of Scope)
- No live unverified web scraping or fragile live API scraping in core inference paths.
- No heavy deep neural networks or multi-agent LLM systems where simple tree ensembles provide clear tabular interpretability.
- No user accounts, billing, tracking, or mobile app stores.
- No claims of navigational safety, sea state hazard assessment, or maritime routing.

