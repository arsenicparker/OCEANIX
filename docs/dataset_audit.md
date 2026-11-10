# OCEANIX Dataset Audit

*Rechecked 9 November 2026. The machine-readable audit is saved at `data/processed/dataset_audit.json`.*

## Audit decision

| Candidate | Verification result | Decision for this stage |
|---|---|---|
| Current INCOIS PFZ sector exports | 14 source exports; 522 prepared points; all source checksums match the dated manifest; all 14 sector labels and coordinates validate | **GO** for a dated advisory data playground and map. **NO-GO** for supervised ML from this snapshot alone. |
| INCOIS PFZ WebGIS line export | 102 valid `MultiLineString` features over 14 sectors; embedded source date is 8 Nov 2026 (Julian day 312), not the same date as the 9 Nov sector export | Retain for investigation; exclude from the current point overlay pending date alignment. |
| Archived Karnataka PFZ Excel | 24 valid positive points, forecast 4–5 Oct 2026; no environmental features or comparison labels | Historical parsing fixture only; not an ML training set. |
| NOAA/NCEI 0306675 | Checksums match; 66,520 rows per raw table; 100% key match; 19,866 non-null SKJ target rows; 12 environmental variables; 2005–2019 | **GO** as a WIO skipjack research dataset only. Retain as reference/fallback; it does not validate Karnataka PFZ. |
| Current environmental inputs from INCOIS | Holdings page lists near-real-time products. The accessible ERDDAP SST/chlorophyll entries inspected here end in 2011, 2020, or earlier; no current gridded environmental extract was added | Open data-access task. Do not label old data as real-time. |

## Current INCOIS snapshot checks

- **Source date:** 9 Nov 2026, source-reported update `Mon Nov 09 16:50:51 IST 2026`.
- **Validity:** Source text says likely availability through 10 Nov 2026.
- **Raw exports:** 14 `.xls` files named `INCOIS_PFZ_SEC001_2026-11-09.xls` through `SEC014`.
- **Manifest:** `data/raw/INCOIS_PFZ_sector_manifest_2026-11-09.json` records sector count, point count, bytes, update text, validity text, and SHA-256 for each export.
- **Prepared table:** 522 unique advisory points across 14 sectors. Coordinates are within latitude −90°..90° and longitude −180°..180°.
- **Bounds:** latitude 6.781111°..22.860278°; longitude 68.660000°..93.639722°.
- **Output:** `data/interim/incois_current_pfz.csv` and `data/interim/incois_current_pfz.geojson`.
- **Audit status:** PASS; 14/14 files found; no checksum mismatch.
- **Freshness:** Dated source snapshot only. The local app does not poll INCOIS. After the forecast validity, refresh the source snapshot before describing it as current.

The official advisory point list represents INCOIS advisories. It does not identify fish absence at unlisted coordinates. The dated snapshot does not contain a measured catch target or environmental feature matrix.

## Current WebGIS line layer checks

`data/raw/INCOIS_PFZ_Lines_India_2026-11-09.geojson` is a valid JSON `FeatureCollection` with 102 `MultiLineString` features and all 14 sector names. Its features have `Year=2026` and `Julian_day=312`, corresponding to 8 November 2026. Its SHA-256 is `2134c80e94e794cc1c2381616b3987502329430d84103ea5c84f23907164a413`.

The line layer’s date and geometry type differ from the sector Excel point export. It is not treated as a matching same-day PFZ boundary layer and is not included in the first map view.

## Historical WIO validation

The audit rechecked the local NOAA files and processed table:

- `Catch_data.txt`: 66,520 rows; 19,866 non-null `SKJ` observations; 46,654 rows with no target.
- `Environmental_data.txt`: 66,520 rows and 12 environmental variables.
- Join on `ID`, `Lon`, `Lat`, `month`, `year`: 66,520 matches; 0 unmatched rows.
- `clean_fishery_env.csv`: 19,866 rows with observed target and 20 columns.
- Chronological split: train 13,599 rows (2005–2015); holdout 6,267 rows (2016–2019); no year crosses both splits.
- Raw file hashes match the previously recorded checksums.

These checks confirm local file integrity and data alignment, not the suitability of the WIO model for the new INCOIS app.

## Required next decision for AIML

Before building an INCOIS model, obtain historical PFZ labels and matched SST/chlorophyll (or other justified environmental variables) for sufficient times and locations. Document source access, target semantics, spatial/temporal matching, coverage, missingness, and defensible comparison samples. A missing advisory label must not be silently interpreted as no fish.

If no usable history and matched features can be obtained, record NO-GO for supervised INCOIS training and agree a revised target or study route before implementing model behavior.
