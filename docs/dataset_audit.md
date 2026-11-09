# OCEANIX Dataset Audit & Evidence Report

*Document Version 1.0 — Milestone M1 (Data Audit)*  
*Conducted in accordance with Project Blueprint Section 7, 8, and Implementation Plan M1.*

---

## 1. Executive Summary & Audit Decisions

In accordance with the Project Blueprint's **"Evidence before algorithms"** rule, candidate datasets were audited before committing to machine learning model architecture or target formulation.

| Candidate Route | Dataset | Audit Outcome | Formal Decision | Operational Role in OCEANIX |
|---|---|---|---|---|
| **Route A** | INCOIS Karnataka PFZ Advisory (`PfzForecast_KARNATAKA.xls`) | 24 operational points, 0 negative examples, 0 environmental features, 48-hour time horizon. | **NO-GO for standalone ML training**<br>**GO for Advisory Parsing & UI Map Overlay** | Preserved and integrated into the frontend Leaflet map and API as an operational advisory overlay; establishes DMS-to-decimal coordinate parsing pipeline. |
| **Route B** | NOAA/NCEI Accession 0306675 (`Catch_data.txt` & `Environmental_data.txt`) | 66,520 total records, 19,866 verified historical catch observations, 12 oceanographic variables, 15 continuous years (2005–2019), 100% inner join match (0 unmatched rows). | **GO for Machine Learning** | Primary machine learning training and evaluation dataset for Western Indian Ocean skipjack tuna suitability and catch biomass modeling. |

---

## 2. Mandatory Dataset Audit Checklist (Blueprint Section 7)

| Check | Required Evidence | Evaluation & Finding | Pass / Status |
|---|---|---|:---:|
| **Identity and Provenance** | Official URL, dataset title, version, retrieval date | Sourced from NOAA/NCEI Accession 0306675 (BCSS / IOTC / Copernicus Marine) and INCOIS Ministry of Earth Sciences. URLs and SHA-256 checksums documented in `docs/data_sources.md`. | **PASS** |
| **Time Coverage** | Earliest/latest timestamp, time zone, frequency | NOAA 0306675 spans 2005 to 2019 (15 full calendar years) at monthly frequency. Allows strict chronological train/test splitting (e.g. 2005–2015 train, 2016–2019 frozen holdout). INCOIS file covers 4–5 Oct 2026. | **PASS** (Route B) |
| **Geography** | Coordinate bounds, CRS, spatial bounds | Western Indian Ocean grid: Longitude [38.75°E, 79.75°E], Latitude [-14.75°S, 14.75°N] in WGS84 decimal degrees. Karnataka PFZ covers Lat [13.18°N, 14.72°N], Lon [73.48°E, 74.52°E]. | **PASS** |
| **Schema and Units** | Column names, field definitions, units, encodings | Documented data dictionary in `data_sources.md`: SST (`thetao` in °C), Salinity (`so` in PSU), Chlorophyll-a (`chl` in $mg/m^3$), Oxygen (`o2` in $mmol/m^3$), Mixed Layer Depth (`mlotst` in m), Currents (`uo`, `vo` in $m/s$). Target `SKJ` in metric tons. | **PASS** |
| **Target Validity** | How target is measured or constructed | Route B target `SKJ` is recorded Skipjack tuna catch biomass from official IOTC fishery logbooks. Target is numeric and empirical. Route A contains only advisory coordinates (no fish abundance). | **PASS** (Route B) |
| **Feature Match** | Join key, time window, spatial matching | Catch records join to Environmental grid exactly on composite key `['ID', 'Lon', 'Lat', 'month', 'year']`. 66,520 rows in both files; 100% match rate, 0 unmatched rows. | **PASS** |
| **Sample Quality** | Row count, duplicates, missingness, impossible values | Zero duplicate composite keys. 19,866 observed catch rows. Predictor null rates: physical variables (0.9%), biogeochemical variables (0.9%), `nppv` (16.5%). Imputation handled strictly post-split. | **PASS** |
| **Class Balance / Distribution** | Target distribution / range | `SKJ` range: 0.19 to 1395.19 metric tons (median: 26.97, IQR: [12.02, 58.37]). Positive right-skewed distribution suitable for log1p transformation or suitability quantile framing. | **PASS** |
| **Data Rights** | License, use terms, citations | NOAA open federal repository / CC0 equivalent; Copernicus open access policy; IOTC data dissemination policy. Proper citation mandatory in all deliverables. | **PASS** |
| **Repeatability** | Deterministic scripts, immutable raw files, checksums | Reproducible via `python src/oceanix/data/audit.py`. SHA-256 checksums recorded; automated test suite verifies integrity. | **PASS** |

---

## 3. Detailed Audit of Route A: INCOIS Karnataka PFZ Advisory

### 3.1 Raw Ingestion & Physical Structure
- **File**: `data/raw/PfzForecast_KARNATAKA.xls`
- **Format**: Microsoft Excel BIFF8 compound binary file.
- **Header Structure**: Metadata in rows 0–1; column headers in row 2; records in rows 3–26; footer abbreviations in rows 27–30.
- **Valid Advisory Points**: Exactly 24 points.

### 3.2 Geographic & Coordinate Audit
Coordinates are supplied in Degree Minute Second (DMS) string format:
- Latitude: `13 10 36 N` to `14 43 18 N` $\rightarrow$ Decimal Degrees: $[13.1767^\circ\text{N}, 14.7217^\circ\text{N}]$
- Longitude: `73 37 15 E` to `74 30 57 E` $\rightarrow$ Decimal Degrees: $[73.4819^\circ\text{E}, 74.5158^\circ\text{E}]$
- Shore Distance: 23 km to 101 km.
- Water Depth: 32 m to 112 m.

### 3.3 Target & Feasibility Analysis
- **Absence of Negative Samples**: The file contains exclusively positive advisory locations. Treating unlisted points as "absence of fish" would be scientifically invalid (violating Blueprint Section 7).
- **Absence of Oceanographic Covariates**: The file contains no paired SST, chlorophyll-a, or salinity values.
- **Conclusion**: Cannot support training a generalized supervised machine learning classifier. It serves as a real-world validation fixture for operational parsing and map visualization.

---

## 4. Detailed Audit of Route B: NOAA/NCEI Accession 0306675

### 4.1 Ingestion & Join Alignment
- **Files**: `Catch_data.txt` (66,520 rows, 6 columns) and `Environmental_data.txt` (66,520 rows, 17 columns).
- **Join Keys**: `ID`, `Lon`, `Lat`, `month`, `year`.
- **Join Outcome**:
  - Inner join row count: **66,520**.
  - Unmatched catch rows: **0**.
  - Unmatched environmental rows: **0**.

### 4.2 Target Field (`SKJ`) Distribution Analysis
- **Observed Fishery Records (`SKJ` is not null)**: **19,866 records** spanning 2005 through 2019.
- **Unobserved Spatial Projection Cells (`SKJ` is null)**: **46,654 records** concentrated in 2014 and 2015, representing the authors' full spatial background grid for Western Indian Ocean mapping.
- **Non-Null Catch Statistics**:
  - Min: 0.19 MT
  - 25th Percentile: 12.02 MT
  - Median (50th): 26.97 MT
  - Mean: 46.49 MT
  - 75th Percentile: 58.37 MT
  - Max: 1,395.19 MT
  - Standard Deviation: 58.46 MT

### 4.3 Environmental Predictor Covariates
Evaluated across the 19,866 observed fishery records:
| Variable | Description | Count Non-Null | Null % | Mean | Min | Median | Max |
|---|---|---|---|---|---|---|---|
| `thetao` | SST (°C) | 19,271 | 2.99% | 27.92 | 24.71 | 28.07 | 30.26 |
| `chl` | Chlorophyll-a ($mg/m^3$) | 19,271 | 2.99% | 2.56 | 0.06 | 0.14 | 8.08 |
| `so` | Salinity (PSU) | 19,271 | 2.99% | 35.34 | 33.08 | 35.39 | 36.62 |
| `o2` | Dissolved Oxygen ($mmol/m^3$) | 19,271 | 2.99% | 202.32 | 190.06 | 201.92 | 221.34 |
| `mlotst` | Mixed Layer Depth (m) | 19,271 | 2.99% | 19.89 | 9.73 | 16.93 | 68.42 |
| `uo` | Eastward velocity ($m/s$) | 19,271 | 2.99% | 0.001 | -0.87 | -0.018 | 0.99 |
| `vo` | Northward velocity ($m/s$) | 19,271 | 2.99% | 0.024 | -1.25 | 0.039 | 0.90 |
| `ph` | Surface pH | 19,271 | 2.99% | 8.028 | 8.002 | 8.027 | 8.080 |
| `zos` | Sea surface height (m) | 19,271 | 2.99% | 0.350 | 0.068 | 0.345 | 0.839 |
| `bottomT` | Bottom temperature (°C) | 19,271 | 2.99% | 1.375 | 0.690 | 0.979 | 28.72 |
| `phyc` | Phytoplankton carbon | 19,271 | 2.99% | 1.374 | 0.854 | 1.325 | 2.976 |
| `nppv` | Net primary production | 16,583 | 16.53% | 6.333 | 0.326 | 2.515 | 50.59 |

---

## 5. Formal Stop/Go Decisions & Synthesis

1. **Route B (NOAA Accession 0306675) is awarded GO status** for machine learning pipeline development. It satisfies all 10 criteria of the blueprint audit checklist, provides a genuine empirical target (`SKJ`), and contains 15 years of matched Copernicus Marine environmental covariates across 19,866 observations.
2. **Route A (INCOIS Karnataka PFZ) is awarded CONDITIONAL-GO**: Classified as **NO-GO for standalone model training**, but **GO for operational advisory parsing, API serving, and Leaflet map rendering**.
3. **Execution Plan**: The machine learning model will be trained on Route B data with explicit labeling that it represents Western Indian Ocean Skipjack Tuna. The web prototype will present predictions for this validated model, while providing the capability to view historical INCOIS coastal advisories with distinct markers and disclaimers.

