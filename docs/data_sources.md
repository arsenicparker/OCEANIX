# OCEANIX Data Sources & Provenance Registry

*Updated 10 November 2026. Raw source files are preserved; prepared app files are derived outputs.*

## 1. Primary source for the data playground: INCOIS PFZ

- **Source organization:** Indian National Centre for Ocean Information Services (INCOIS), Ministry of Earth Sciences, Government of India.
- **Official PFZ service:** [Potential Fishing Zone Advisory](https://www.incois.gov.in/MarineFisheries/PfzAdvisory)
- **Text-sector page:** [INCOIS marine fisheries text advisories](https://www.incois.gov.in/MarineFisheries/TextDataHome?mfid=1&request_locale=en)
- **Interactive official map:** [INCOIS PFZ WebGIS](https://www.incois.gov.in/MarineFisheries/PfzWebGis)
- **Access method:** INCOIS’s own sector text page and spreadsheet export; no API key was used.
- **Snapshot retrieved:** 9 Nov 2026. Sector page reported update time `Mon Nov 09 16:50:51 IST 2026`; displayed forecast text states likely availability through 10 Nov 2026.
- **Coverage:** All 14 sector exports. The prepared table contains 522 advisory locations. Counts by sector are recorded in `data/raw/INCOIS_PFZ_sector_manifest_2026-11-09.json`.
- **Coordinates:** Raw exports use DMS. The parser also supports decimal-degree variants. DMS was selected for this snapshot to retain source precision.
- **Raw files:** `data/raw/INCOIS_PFZ_SEC001_2026-11-09.xls` through `SEC014`; every downloaded file has a size and SHA-256 in the manifest.
- **Prepared outputs:** `data/interim/incois_current_pfz.csv` and `data/interim/incois_current_pfz.geojson`.
- **Freshness rule:** This is a dated snapshot, not a live app connection. Check source dates and refresh the snapshot before describing it as current after its validity date.

The daily advisory points are official INCOIS output, not OCEANIX model predictions. A PFZ advisory is a potential aggregation advisory and is not a fish-count observation, catch guarantee, or safety forecast.

### INCOIS WebGIS line export

- **Raw file:** `data/raw/INCOIS_PFZ_Lines_India_2026-11-09.geojson`
- **Service:** INCOIS public GeoServer WFS layer `PFZ_Automation:pfzlines`.
- **Retrieved:** 9 Nov 2026; SHA-256 `2134c80e94e794cc1c2381616b3987502329430d84103ea5c84f23907164a413`.
- **Contents:** 102 `MultiLineString` features across 14 sector labels.
- **Embedded date:** Every feature records `Year=2026`, `Julian_day=312` (8 Nov 2026). This is one day earlier than the 9 Nov sector export and its 9–10 Nov forecast. It is stored for investigation but is not overlaid on the current advisory points in the playground.

## 2. INCOIS environmental products and the ML data gap

INCOIS [Data Holdings](https://www.incois.gov.in/site/dataholdings.jsp) lists near-real-time PFZ advisories, satellite SST/chlorophyll products, and other ocean observations. The PFZ service describes its satellite SST and chlorophyll inputs. However, a holdings listing does not by itself establish a usable, downloadable, spatially and temporally matched dataset.

The public [INCOIS ERDDAP catalog](https://erddap.incois.gov.in/erddap/tabledap/allDatasets.html) was checked on 9 Nov 2026. Relevant active entries inspected from the catalog included:

| Catalog entry | Variables relevant here | Catalog time coverage observed | Finding |
|---|---|---|---|
| `NOAA_AVHRR_AMSR_datasets` | Daily SST and SST anomaly | 2002-06-01 to 2011-10-04 | Historical, not current |
| `incois_oceansat2_datasets` | INCOIS Oceansat-2 ocean-colour data | 2011-02-02 to 2020-05-01 | Historical, not current |
| `IRS_chlorophyll_datasets` | Chlorophyll | 2003-01-05 to 2006-03-21 | Historical, not current |
| `incois_argo_sst_weekly` | Argo SST | 2009-01-07 to 2010-12-29 | Historical, not current |

These ERDDAP archive entries do not provide current SST/chlorophyll point series. The operational [INCOIS Ocean State Forecast](https://iioe-2.incois.gov.in/oceanservices/osfforecast.jsp) page separately publishes dated THREDDS WMS products and provides `GetTimeseries` point queries for SST, currents, mixed-layer depth (MLD), D20, wind, and wave fields. The app discovers the current product filenames from that page, queries the selected INCOIS advisory coordinate, and reports each source timestamp. These values are model forecast fields, not in-situ measurements. Network/service failures and missing ocean cells are shown as unavailable.

INCOIS [ABIS](https://incois.gov.in/site/services/hab_products.jsp) publishes daily 4 km chlorophyll-a and SST satellite map products, plus a NetCDF download. The current map is shown in Ocean Conditions with its publication date and color scale. The public page does not expose a supported point-value query for the selected coordinate, so the app does not turn image colors into a numeric chlorophyll reading. The ERDDAP Oceansat-2 chlorophyll series inspected above ends in 2020 and is not used as a live substitute.

The OSF query cache is 10 minutes. Product availability and timestamps depend on INCOIS; these operational endpoints are not guaranteed to be uninterrupted. Neither the OSF forecasts nor the ABIS chlorophyll map is an OCEANIX catch prediction or a guarantee of fish presence.

**Open data task:** determine whether INCOIS provides downloadable historical PFZ labels and environmental fields with adequate coverage and reuse terms. Until then, supervised INCOIS model training is NO-GO.

## 3. Previously collected Karnataka PFZ fixture

- **File:** `data/raw/PfzForecast_KARNATAKA.xls`
- **Snapshot:** 4–5 Oct 2026, 24 positive advisory points.
- **SHA-256:** `2d532086e0601a9875fb32ebc435844c5c4c8e6fc1c91b1f8dc3f6871d436378`.
- **Prepared outputs:** `data/interim/cleaned_incois_karnataka.csv` and `.geojson`.
- **Role:** Historical parsing/test fixture. It has no environmental predictors or defensible comparison labels, so it cannot train a standalone classifier.

## 4. Retained WIO historical dataset (reference/fallback)

- **Dataset:** NOAA/NCEI Accession 0306675, 2005–2019 Western Indian Ocean skipjack tuna and marine environment time series.
- **Catalog:** [NOAA/NCEI accession](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.nodc:0306675)
- **Raw files:** `Catch_data.txt` and `Environmental_data.txt`; the local `NCEI-Readme.txt` is 1,888 bytes.
- **Local SHA-256 checks:** catch `4f9e4cdd8d8c65d55ef5c5fb460a43b3ea3cd35cecd2b00f305f576bc3da317c`; environment `0613e8aeef0d9ee9ddf42634712341b7f312930ca5c21275e2affdbf1b61082a`.
- **Verified raw dimensions:** 66,520 rows in each file; composite-key inner join matches all 66,520 rows. `SKJ` has 19,866 non-null catch records and 46,654 null projection cells. Processed table contains only the observed-target rows.
- **Processed file:** `data/processed/clean_fishery_env.csv`, 19,866 rows, 20 columns; train 13,599 (2005–2015), holdout 6,267 (2016–2019).
- **Role:** Retained for reproducibility and possible rescoping. Its catch labels are not Karnataka PFZ labels and it is not used by the INCOIS playground.

The local source-file hashes and counts were rechecked with `src/oceanix/data/audit.py`. Do not present this WIO dataset as validation for Karnataka coastal fisheries.

## 5. Raw-data handling

1. Do not edit raw source exports in place.
2. Keep dated snapshots and manifests so later refreshes do not erase provenance.
3. Recompute checksums and run the dataset audit after each refresh.
4. Store transformations only under `data/interim/` or `data/processed/`.
5. Attribute INCOIS and all other providers near any displayed data or map layer.
