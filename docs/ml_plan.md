# OCEANIX Machine Learning Plan

*Document Version 1.0 — Milestone M3 (Machine Learning)*  
*Prepared strictly according to Project Blueprint Section 10.*

---

## 1. Task Definition
- **Task Type**: Supervised Regression with log-transformed target.
- **Target Variable**: `skipjack_catch_biomass` (Skipjack tuna catch biomass in Metric Tons per monthly $0.5^\circ$ cell).
- **Study Domain**: Western Indian Ocean (WIO), bounding box [38.75°E–79.75°E, -14.75°S–14.75°N].
- **Observation Unit**: Grid cell / monthly aggregate with paired Copernicus oceanographic reanalysis.

---

## 2. Feature Architecture

| Feature Group | Features | Role & Justification |
|---|---|---|
| **Spatio-Temporal** | `longitude`, `latitude`, `month` | Captures geographic coordinates and seasonal cycles. |
| **Thermal & Physical** | `thetao` (SST), `bottomT`, `so` (Salinity), `mlotst` (MLD), `zos` (SSH) | Defines ocean physical structures, thermoclines, and water mass boundaries. |
| **Dynamic Currents** | `uo` (Zonal current), `vo` (Meridional current) | Models advection, convergence zones, and surface flow. |
| **Biogeochemical & Trophic** | `chl` (Chlorophyll-a), `phyc` (Phytoplankton), `nppv` (NPP), `o2` (Oxygen), `ph` | Measures primary productivity, biological aggregation, and dissolved oxygen availability. |

---

## 3. Preprocessing & Leakage Prevention
- **Imputation**: Numeric median imputation fitted **exclusively** on the training partition via `sklearn.compose.ColumnTransformer`.
- **Target Transformation**: `TransformedTargetRegressor` applying $y' = \ln(1 + y)$ during training and $\hat{y} = \exp(\hat{y}') - 1$ at inference. This stabilizes variance across extreme catch values without creating artificial negative predictions.
- **Partitioning**: Strictly chronological split at cutoff year $\le 2015$ (Training: 2005–2015; Holdout Test: 2016–2019). No random k-fold splitting across dates to prevent spatial/temporal autocorrelation leakage.

---

## 4. Modeling Sequence & Acceptance Thresholds
1. **Baseline Model**: `DummyRegressor(strategy='median')` provides the required benchmark.
2. **Primary Candidate**: `RandomForestRegressor(n_estimators=100, max_depth=12, min_samples_leaf=5)` to capture nonlinear interactions between physical variables and tuna aggregation.
3. **Acceptance Threshold**: The primary candidate must outperform the baseline on held-out test MAE and RMSE before deployment to the API.

