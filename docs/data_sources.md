# OCEANIX Data Sources & Provenance Registry

*Document Version 1.0 — Milestone M1 (Data Audit)*  
*Prepared strictly according to Project Blueprint Section 6 & 7.*

---

## 1. Overview
This registry catalogs all raw datasets acquired for OCEANIX. Each dataset is preserved in `data/raw/` as an immutable source file. Any modification is performed exclusively via deterministic preprocessing pipelines in `src/oceanix/data/`.

---

## 2. Source Inventory & Lineage

### Source 1: NOAA/NCEI Accession 0306675 (Western Indian Ocean Skipjack Tuna & Environment)
- **Official Title**: Weather, Ocean, and Tuna biomass time-series from 2005–2019 in the Western Indian Ocean (WIO) region (NCEI Accession 0306675)
- **Originating Organization**: National Oceanic and Atmospheric Administration (NOAA) / National Centers for Environmental Information (NCEI)
- **Data Provider**: Ms. Norton Cossa, Bazaruto Centre for Scientific Studies (BCSS) via Send2NCEI (S2N package MEXPML)
- **Primary Fishery Data Source**: Indian Ocean Tuna Commission (IOTC) historical catch records
- **Primary Environmental Data Source**: Copernicus Marine Service (CMEMS) numerical ocean model reanalysis
- **Access Date**: 9 November 2026
- **Metadata URLs**:
  - NOAA Landing Page: `https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.nodc:0306675`
  - Data.gov Catalog: `https://catalog.data.gov/dataset/weather-ocean-and-tuna-biomass-time-series-from-2005-2019-in-the-western-indian-ocean-wio-`
  - Direct Archive: `https://www.ncei.noaa.gov/data/oceans/archive/arc0235/0306675/1.1/data/0-data/`
- **License / Rights**: Open Access / Public Domain (U.S. Federal Government work & international open scientific repository). Standard attribution to NOAA/NCEI, IOTC, and Copernicus Marine Service.

#### Raw Files & Checksums
| File Name | Size (Bytes) | SHA-256 Checksum | Format | Description |
|---|---|---|---|---|
| `Catch_data.txt` | 2,164,923 | `4f9e4cdd8d8c65d55ef5c5fb460a43b3ea3cd35cecd2b00f305f576bc3da317c` | Text (Whitespace-delimited) | 66,520 records containing ID, Lon, Lat, month, year, and SKJ catch |
| `Environmental_data.txt` | 14,889,328 | `0613e8aeef0d9ee9ddf42634712341b7f312930ca5c21275e2affdbf1b61082a` | Text (Whitespace-delimited) | 66,520 records containing ID, Lon, Lat, month, year, and 12 marine physical/biogeochemical variables |
| `NCEI-Readme.txt` | 1,847 | — | Plain Text | NCEI archival information package description |

#### Field Dictionary (Environmental & Catch)
| Field | Type | Unit | Description / Meaning |
|---|---|---|---|
| `ID` | Integer | — | Unique observation/grid identifier |
| `Lon` | Float | Decimal Degrees | Longitude (38.75°E to 79.75°E) |
| `Lat` | Float | Decimal Degrees | Latitude (-14.75°S to 14.75°N) |
| `month` | Integer | Month (1–12) | Observation calendar month |
| `year` | Integer | Year (2005–2019) | Observation calendar year (15 full years) |
| `SKJ` | Float | Metric Tons | Skipjack tuna (*Katsuwonus pelamis*) catch biomass per month/grid cell |
| `ph` | Float | pH scale | Ocean sea surface pH |
| `nppv` | Float | $mg \cdot C \cdot m^{-3} \cdot day^{-1}$ | Net primary production of biomass |
| `phyc` | Float | $mmol \cdot C \cdot m^{-3}$ | Phytoplankton expressed as carbon |
| `chl` | Float | $mg \cdot m^{-3}$ | Chlorophyll-a mass concentration in sea water |
| `o2` | Float | $mmol \cdot m^{-3}$ | Dissolved oxygen concentration in sea water |
| `so` | Float | PSU | Sea surface salinity |
| `mlotst` | Float | Meters (m) | Ocean mixed layer thickness (MLD) |
| `uo` | Float | $m/s$ | Eastward sea water velocity (zonal current) |
| `vo` | Float | $m/s$ | Northward sea water velocity (meridional current) |
| `thetao` | Float | °Celsius | Sea surface potential temperature (SST) |
| `bottomT` | Float | °Celsius | Sea water potential temperature at sea floor |
| `zos` | Float | Meters (m) | Sea surface height above geoid (SSH) |

---

### Source 2: INCOIS Karnataka PFZ Operational Advisory
- **Official Title**: Potential Fishing Zone (PFZ) Advisory — Karnataka Sector
- **Originating Organization**: Indian National Centre for Ocean Information Services (INCOIS), Ministry of Earth Sciences, Government of India
- **Access Date**: 4 October 2026 (Archived locally in `data/raw/`)
- **Official Portal**: `https://www.incois.gov.in/MarineFisheries/PfzAdvisory`
- **License / Rights**: Official government advisory for public benefit and fisher safety/decision-support. Non-commercial scientific and educational reuse.

#### Raw File & Checksum
| File Name | Size (Bytes) | SHA-256 Checksum | Format | Description |
|---|---|---|---|---|
| `PfzForecast_KARNATAKA.xls` | 8,704 | `2d532086e0601a9875fb32ebc435844c5c4c8e6fc1c91b1f8dc3f6871d436378` | Microsoft Excel (BIFF8) | Single operational forecast containing 24 advisory points with coastal bearings, distances, and DMS coordinates |

#### Field Dictionary (INCOIS Advisory)
| Field | Type | Example | Description / Meaning |
|---|---|---|---|
| `From the coast of` | String | "Belekeri", "Karwar", "Malpe" | Coastal landing center reference point |
| `Direction` | String | "NW", "SW" | Direction from coastal landing reference |
| `Bearing (deg)` | Integer / String | 271, 236 | Compass bearing in degrees from reference station |
| `Distance (km) From-To`| String | "67-72", "25-30" | Distance range in kilometers from shore |
| `Depth (mtr) From-To` | String | "56-61", "46-51" | Water depth range in meters at advisory zone |
| `Latitude (dms)` | String | "14 43 18 N" | Advisory point latitude in Degrees Minutes Seconds |
| `Longitude (dms)` | String | "73 37 15 E" | Advisory point longitude in Degrees Minutes Seconds |
| `Forecast Validity` | Date Window | "4 Oct 2026 to 5 Oct 2026" | Operational validity window (48 hours) |

---

## 3. Storage & Integrity Rules
1. Files in `data/raw/` are **read-only** and never edited in-place.
2. Checksums must be verified prior to running data preparation pipelines.
3. Cleaned datasets are written to `data/interim/` and `data/processed/`.

---

## 4. Prepared & Model-Ready Tables (Milestone M2)

### Processed Output 1: `data/processed/clean_fishery_env.csv`
- **Source**: Inner join of `Catch_data.txt` and `Environmental_data.txt` with unobserved background grid cells excluded.
- **Row Count**: 19,866 observed fishery catch events.
- **Columns**: 20 (Observation metadata, spatio-temporal coordinates, target catch biomass, split flag, and 12 environmental features).
- **Target Variable**: `skipjack_catch_biomass` (Metric Tons). Range: 0.19 to 1395.19 MT (Median: 26.97 MT).
- **Temporal Partitions**:
  - `train` split (2005–2015): 13,599 rows (68.45%).
  - `test` holdout split (2016–2019): 6,267 rows (31.55%).
- **Metadata Log**: `data/processed/split_metadata.json`.

### Interim Output 2: `data/interim/cleaned_incois_karnataka.csv` & `.geojson`
- **Source**: Deterministic extraction from `PfzForecast_KARNATAKA.xls`.
- **Row Count**: 24 operational advisory points.
- **Coordinates**: Converted from Degree-Minute-Second (DMS) to Decimal Degrees (DD).
- **Format**: CSV table and RFC 7946 GeoJSON FeatureCollection for Leaflet map overlay.


