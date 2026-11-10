# OCEANIX Implementation Plan

*Revised 10 November 2026 to reflect the mobile-first UI, point-specific INCOIS conditions, and local phone access.*

## Project direction

OCEANIX is a mobile-first responsive web app. The current build expands the data playground toward the reference UI: dashboard, region search, advisory results, interactive map, snapshot insights, history, About, and Settings. It shows official INCOIS advisories and a point-concentration heat layer. The heat colors represent where advisory points cluster, not catch probability or an OCEANIX prediction.

The primary user-facing data source is the official INCOIS Potential Fishing Zone (PFZ) advisory. A dated snapshot for all 14 INCOIS sectors has been downloaded and audited. Ocean Conditions now queries the operational INCOIS Ocean State Forecast products at a selected advisory coordinate and displays the daily ABIS chlorophyll-a map. OSF fields are model forecasts; the ABIS image is satellite data. Later, a supervised AIML model may be added only after a historical PFZ archive and matched environmental data pass an audit. The existing WIO files and model notes are retained as a reference/fallback, not as the current app’s advisory source.

## Current dataset status

| Dataset | Local status | Verified use |
|---|---|---|
| INCOIS PFZ sector exports | 14 dated Excel exports from 9 Nov 2026; DMS coordinates; 522 points total; checksums in `data/raw/INCOIS_PFZ_sector_manifest_2026-11-09.json` | Data playground and map |
| INCOIS PFZ WebGIS lines | 102 MultiLineString features; source fields identify 8 Nov 2026 (Julian day 312) | Stored for investigation; excluded from the 9 Nov point map until dates are reconciled |
| Earlier Karnataka PFZ export | One archived forecast from 4–5 Oct 2026; 24 points | Historical parsing fixture only |
| NOAA/NCEI 0306675 WIO catch/environment | Existing files and processed table retained; checksums, row counts, joins, and split rechecked | Legacy WIO reference/fallback; not a Karnataka model |
| INCOIS Ocean State Forecast (OSF) point time series | Operational WMS `GetTimeseries` products discovered from the official OSF page: SST, surface current, MLD, D20, wind, wave height, and wave period | Fetched for a selected advisory coordinate; shown with timestamp and identified as model forecast; 10-minute API cache |
| INCOIS ABIS daily satellite products | Regional 4 km chlorophyll-a and SST maps, plus a daily NetCDF download; page inspected 10 Nov 2026 | Chlorophyll map and publication date shown; no numeric selected-pixel value until a supported and verified point query is available |
| Older INCOIS ERDDAP chlorophyll/SST archives | Catalog entries inspected on 9 Nov 2026 end in 2020 or earlier | Not used as current environmental readings |

The point snapshot is valid through 10 Nov 2026 according to the source export. It is a saved snapshot, not a continuously refreshed feed. Refresh it from the official source before presenting it as current on a later date.

## Milestone 0 — Repository and data audit (completed for this revision)

- [x] Inspect repository, docs, API, frontend, raw datasets, processed tables, and existing tests.
- [x] Recompute the three existing raw-file hashes; all match the prior source registry.
- [x] Recheck the NOAA/NCEI row counts, target coverage, time range, and processed chronological split.
- [x] Retrieve the current official INCOIS sector exports for all 14 sectors using the site’s spreadsheet export.
- [x] Retain DMS coordinates and write a per-file SHA-256 manifest.
- [x] Prepare a combined 522-point CSV and GeoJSON; validate coordinate ranges and all 14 sector labels.
- [x] Retrieve the official PFZ WebGIS line export and record its separate embedded date.
- [x] Record the accessible INCOIS environmental products and the mismatch between the holdings summary and active ERDDAP dataset dates.

## Milestone 1 — INCOIS data foundation (completed)

### Scope

- Show a compact, responsive OCEANIX page with an INCOIS source date, validity note, dataset counts, and a map.
- Filter advisory points by sector and landing centre; keep the map, table, and count in sync.
- Use OpenStreetMap tiles with attribution so local map display does not require a CARTO key.
- Serve prepared local GeoJSON and summary metadata through FastAPI.
- Make it clear that the visible points are official INCOIS advisories, not OCEANIX model predictions.
- Preserve source dates, provenance, and the distinction between official advisories and future model output.

### Acceptance checks

- API summary reports the snapshot date, point count, and sector count from the prepared data.
- Map markers and table rows come from the same API response and respond to the same filters.
- Selecting a table row locates the point on the map.
- The UI names the snapshot and its validity, and links to the official INCOIS advisory and WebGIS.
- Map tiles use a keyless source with visible attribution; tile failures show a readable message.
- No user-entered ocean measurements or uncalibrated confidence percentage are presented.
- The foundation checks passed during the earlier data-playground revision. The expanded UI still needs a phone and desktop visual review.

## Milestone 2 — Historical INCOIS dataset feasibility (blocked on source availability, not on coding)

1. Locate a machine-readable archive of historical PFZ advisories and document retrieval terms, dates, sectors, and formats.
2. Locate historical SST/chlorophyll (and other justified variables) for the same areas and periods.
3. Match advisory labels and ocean measurements using a documented spatial and temporal method.
4. Quantify missingness, coverage, class construction, and matching error.
5. Define the target as historical advisory inclusion/pattern only unless independent catch measurements support a stronger target. “Not listed in an advisory” must not be called “no fish.”
6. Record a formal GO / CONDITIONAL GO / NO-GO decision before training.

If these sources cannot be obtained in a defensible form, do not create a supervised model from a single daily snapshot. Reassess whether an explicitly rule-based environmental index or the separately scoped WIO fallback fits the project.

## Milestone 3 — AIML experiment (after Milestone 2 GO)

- Build the model only from verified historical features and labels.
- Compare a simple baseline with one justified estimator.
- Split by time and, where the data supports it, geographic group; report sample counts and leakage checks.
- Report target-specific metrics, weak areas, provenance, and limitations. Do not surface the existing WIO metrics as INCOIS/Karnataka performance.
- Serve model results only when the request can be fulfilled from source-backed app data; do not ask users to invent or enter ocean measurements.

## Milestone 4 — Main mobile-first UI (active)

Build the responsive experience inspired by the screenshot: dashboard, find-zone flow, advisory result state, interactive map with selectable point and advisory-concentration layer, ocean conditions, insights, history/saved regions, About, and Settings. Use the phone layout as the primary design target and make the same flows adapt to desktop. Show environmental products only with source, timestamp, and forecast/satellite labels; do not present catch probabilities before model validation. Keep official advisories distinct from future OCEANIX model outputs.

### Current UI behavior and data limits

- Region search uses a selected INCOIS sector, landing-centre text, or optional browser geolocation. Device coordinates are kept in page memory only and are not sent to the API or saved to history.
- The radius control filters available advisory coordinates around device location; sector or centre searches return matching available advisory points.
- The map heat layer uses equal-weight INCOIS advisory points. Its legend reads “Fewer points” to “More points” and explicitly says it is not catch probability.
- Ocean Conditions requires the user to select an official advisory coordinate, then requests OSF forecast time series and shows per-field timestamps. The daily ABIS chlorophyll map is presented separately; the selected-pixel number remains unavailable because the public page exposes a map product rather than a validated point query.
- On a phone on the same Wi-Fi as the development computer, open the computer’s private IP and app port. The server binds to the local network for this purpose. Browser GPS requires HTTPS; selecting a real INCOIS advisory coordinate works over the local HTTP connection.
- Insights summarize counts in the single available snapshot. They do not imply temporal trends or fish abundance.
- History and saved sector names use browser local storage. Exact device coordinates are not persisted.
- The saved dataset has one date only; the date control therefore exposes the available snapshot date rather than implying historical date search.

The first main UI target remains a mobile-friendly web app. APK packaging can be considered later; it is not part of the data-playground milestone.

## Implementation notes

- Raw source exports are preserved under `data/raw/`; prepared files are written under `data/interim/`.
- The current source snapshot and data-preparation outputs are dated. A future refresh should create a new dated snapshot and manifest rather than overwrite earlier source evidence.
- The map requires an internet connection for OpenStreetMap tiles. The app itself makes no CARTO request and requires no map API key.
- Android starter files were already modified in the working tree before this revision. They were left untouched; native Android work remains deferred.
