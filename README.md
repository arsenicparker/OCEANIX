# OCEANIX — Marine Intelligence Prototype

OCEANIX is an AIML project being built in stages. The current deliverable is a mobile-first responsive web app for exploring official INCOIS Potential Fishing Zone advisories and point-specific ocean conditions. It includes a dashboard, region search, nearby advisory results, interactive map, advisory-concentration heat layer, environmental conditions, snapshot insights, local search history, About, and Settings.

**The current app does not make an OCEANIX fishing prediction and does not accept user-provided ocean measurements.** The map heat layer shows advisory-point concentration, not catch probability. The INCOIS data currently in the repository is a snapshot retrieved on 9 November 2026 and reported valid through 10 November 2026. Refresh and audit the source data before describing it as current at a later date.

## What is available

- 14 INCOIS sector spreadsheet exports in `data/raw/` with a checksum manifest.
- 522 prepared advisory locations in `data/interim/incois_current_pfz.csv` and `.geojson`.
- A FastAPI service for snapshot health, summary, and GeoJSON.
- Ocean Conditions queries INCOIS Ocean State Forecast point time series for SST, surface current, mixed-layer depth, D20, wind, and waves. Each field includes a timestamp and is labelled as a model forecast.
- Ocean Conditions also displays the latest daily INCOIS ABIS chlorophyll-a satellite map when the public product is available. INCOIS currently publishes this as a regional image; the app does not invent a selected-pixel concentration.
- Responsive phone-first views for dashboard, finding zones, results, map, ocean conditions, insights, history, About, and Settings.
- Optional device-location search; coordinates remain in the browser session and are not saved or sent to the API.
- An advisory-concentration heat layer: equal-weight advisory coordinates are shaded by point density. It is not a probability surface.
- A keyless OpenStreetMap base layer with attribution. Internet is required for map tiles and Leaflet resources.
- The previous WIO catch/environment dataset remains in `data/raw/` and `data/processed/` as a separate reference/fallback. It is not used by the current page.

See [`docs/data_sources.md`](docs/data_sources.md) for provenance and files, [`docs/dataset_audit.md`](docs/dataset_audit.md) for verification, and [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) for the staged plan.

## Run locally

Use Python 3.10 or newer. From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m uvicorn oceanix.api.main:app --app-dir src --host 0.0.0.0 --port 8000
```

On the computer, open [http://127.0.0.1:8000](http://127.0.0.1:8000). On the phone, connect to the same Wi-Fi, then open `http://<computer-private-IP>:8000` (for example, `http://192.168.1.20:8000`). Find the private IP with `ipconfig` on Windows. Keep the server running while using the phone; this address is only for your local network and is not an internet deployment. If Windows Firewall blocks it, allow the Python server only for local-network devices on the active Wi-Fi; do not add router port forwarding.

API health is at `/health`; the current INCOIS data summary is at `/api/pfz/current/summary`; the GeoJSON is at `/api/pfz/current`; and selected-location environmental data is at `/api/environment/current?lat=13&lon=74.5`.

Browser geolocation requires a secure context. On a phone using a local `http://<computer-private-IP>` address, choose one of the official advisory points for environmental readings. Device GPS will be available after deploying the app behind HTTPS.

The app uses external Leaflet, Leaflet.heat, and OpenStreetMap resources, but no map API key. If map tiles or the heat-layer library do not load, the app displays a status message and retains the advisory search/list data.

## Rebuild the prepared INCOIS snapshot

Raw exports are immutable. The current prepared files were produced with:

```powershell
python -c "from oceanix.data.prepare import prepare_incois_current_snapshot; prepare_incois_current_snapshot('data/raw', 'data/interim', 'data/raw/INCOIS_PFZ_sector_manifest_2026-11-09.json')"
python src/oceanix/data/audit.py --data-dir data/raw --output data/processed/dataset_audit.json
```

The script combines the dated sector exports present in the manifest, validates coordinates, skips spreadsheet footers, and writes the CSV and GeoJSON. To refresh after 10 Nov 2026, collect a new official snapshot and create a new dated manifest first; the existing snapshot is not a live feed.

## Verification

```powershell
python -m pytest -q --basetemp .pytest_cache/test-tmp
```

Tests cover source hashes and row alignment, current snapshot parsing, API responses, filters’ supporting data, and the keyless map configuration. The AIML model stage is intentionally gated: one INCOIS snapshot cannot train a supervised model. See [`docs/ml_plan.md`](docs/ml_plan.md).

## Project boundaries

- INCOIS points are official advisory locations, not OCEANIX model estimates.
- An unlisted point does not mean fish are absent.
- The current app is not a catch guarantee, safety assessment, or navigation tool.
- The existing NOAA/NCEI data is Western Indian Ocean skipjack data and cannot validate a Karnataka coastal model.
- Historical INCOIS PFZ labels and matched environmental measurements must pass an audit before AIML training starts.
