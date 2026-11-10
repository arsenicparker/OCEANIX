"""FastAPI application for OCEANIX Marine Intelligence Service.

Serves model predictions, metadata, and operational advisory overlays in adherence
with Project Blueprint Section 12, 13, and Implementation Plan M5.
"""

from __future__ import annotations

import json
import logging
import csv
import io
import re
import threading
from datetime import datetime, timezone
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urljoin

import requests
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from oceanix.api.schemas import (
    HealthResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("oceanix.api")
INCOIS_OSF_PAGE = "https://iioe-2.incois.gov.in/oceanservices/osfforecast.jsp"
INCOIS_ABIS_PAGE = "https://incois.gov.in/site/services/hab_products.jsp"
_environment_cache: dict[tuple[float, float], tuple[float, dict[str, Any]]] = {}
_environment_cache_lock = threading.Lock()
_HTTP = requests.Session()
_HTTP.headers.update({"User-Agent": "OCEANIX educational prototype/1.0"})

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
ADVISORY_GEOJSON_PATH = ROOT_DIR / "data" / "interim" / "cleaned_incois_karnataka.geojson"
CURRENT_PFZ_GEOJSON_PATH = ROOT_DIR / "data" / "interim" / "incois_current_pfz.geojson"
CURRENT_PFZ_MANIFEST_PATH = ROOT_DIR / "data" / "raw" / "INCOIS_PFZ_sector_manifest_2026-11-09.json"
CURRENT_PFZ_LINES_PATH = ROOT_DIR / "data" / "raw" / "INCOIS_PFZ_Lines_India_2026-11-09.geojson"

# Global singleton model & metadata container
app_state: Dict[str, Any] = {
    "advisories_geojson": None,
    "current_pfz_geojson": None,
    "current_pfz_manifest": None,
    "current_pfz_lines": None,
}


def load_artifacts() -> None:
    """Load saved INCOIS data snapshots into global state."""
    if app_state.get("advisories_geojson") is None and ADVISORY_GEOJSON_PATH.exists():
        try:
            with open(ADVISORY_GEOJSON_PATH, "r", encoding="utf-8") as f:
                app_state["advisories_geojson"] = json.load(f)
            logger.info("Loaded INCOIS Karnataka advisory GeoJSON from %s", ADVISORY_GEOJSON_PATH)
        except Exception as e:
            logger.error("Failed to load advisory GeoJSON: %s", e)

    # Load the dated all-sector INCOIS snapshot used by the data playground.
    for key, path in (
        ("current_pfz_geojson", CURRENT_PFZ_GEOJSON_PATH),
        ("current_pfz_manifest", CURRENT_PFZ_MANIFEST_PATH),
        ("current_pfz_lines", CURRENT_PFZ_LINES_PATH),
    ):
        if app_state.get(key) is None and path.exists():
            try:
                app_state[key] = json.loads(path.read_text(encoding="utf-8-sig"))
                logger.info("Loaded %s from %s", key, path)
            except Exception as e:
                logger.error("Failed to load %s: %s", key, e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to load model and metadata at startup."""
    logger.info("Initializing OCEANIX API server...")
    load_artifacts()
    yield
    logger.info("Shutting down OCEANIX API server...")


# Pre-load artifacts at import time as well
load_artifacts()

app = FastAPI(
    title="OCEANIX INCOIS Data Playground API",
    description=(
        "Serves a dated, source-attributed INCOIS Potential Fishing Zone advisory snapshot. "
        "This stage does not provide OCEANIX model predictions."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

# Configure CORS for local development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
        "http://10.0.2.2:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    """Confirm the API and prepared INCOIS snapshot are available."""
    load_artifacts()
    geojson = app_state.get("current_pfz_geojson")
    manifest = app_state.get("current_pfz_manifest") or {}
    return HealthResponse(
        status="ok",
        data_loaded=geojson is not None,
        snapshot_date=manifest.get("retrieved_local_date"),
    )


@app.get("/advisories/karnataka", tags=["Advisories"])
def get_karnataka_advisories():
    """Return parsed INCOIS Karnataka operational advisory points as GeoJSON."""
    load_artifacts()
    geojson = app_state.get("advisories_geojson")
    if not geojson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="INCOIS Karnataka advisory GeoJSON not found.",
        )
    return JSONResponse(content=geojson)


@app.get("/api/pfz/current", tags=["INCOIS data"])
def get_current_pfz_snapshot():
    """Return the saved, dated official INCOIS PFZ point snapshot."""
    load_artifacts()
    geojson = app_state.get("current_pfz_geojson")
    if not geojson:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The dated INCOIS PFZ snapshot has not been prepared.",
        )
    return JSONResponse(content=geojson)


@app.get("/api/pfz/current/summary", tags=["INCOIS data"])
def get_current_pfz_summary():
    """Return source dates, sector coverage, and record counts for the snapshot."""
    load_artifacts()
    geojson = app_state.get("current_pfz_geojson")
    manifest = app_state.get("current_pfz_manifest")
    if not geojson or not manifest:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The INCOIS snapshot or its provenance manifest is unavailable.",
        )
    features = geojson.get("features", [])
    sectors = sorted({f.get("properties", {}).get("sector_name") for f in features})
    return {
        "snapshot_date": manifest.get("retrieved_local_date"),
        "source_updated_at": (manifest.get("sectors") or [{}])[0].get("updated"),
        "forecast_validity": (manifest.get("sectors") or [{}])[0].get("validity"),
        "point_count": len(features),
        "sector_count": len(sectors),
        "sectors": sectors,
        "source": manifest.get("source"),
        "coordinate_format": manifest.get("coordinate_format"),
        "is_live_connection": False,
        "note": "Saved official INCOIS snapshot; refresh by collecting a new source export.",
    }


@app.get("/api/pfz/lines", tags=["INCOIS data"])
def get_current_pfz_lines():
    """Return the separately dated WFS line layer for inspection."""
    load_artifacts()
    data = app_state.get("current_pfz_lines")
    if not data:
        raise HTTPException(status_code=404, detail="INCOIS WFS line snapshot not found.")
    return JSONResponse(content=data)


def _current_product_files() -> dict[str, str]:
    """Read current file names from INCOIS's own OSF page (no API key)."""
    response = _HTTP.get(INCOIS_OSF_PAGE, timeout=20)
    response.raise_for_status()
    html = response.text
    names = {}
    for key, variable in {
        "sst": "sstnio",
        "currents": "currentsFile2",
        "mld": "mldnio",
        "waves": "rsmc_combined_ww3",
    }.items():
        match = re.search(rf'\bvar\s+{variable}\s*=\s*["\']([^"\']+)', html)
        if not match:
            raise ValueError(f"INCOIS OSF did not publish a current {key} product filename.")
        names[key] = match.group(1)
    return names


def _read_timeseries(product_url: str, layer: str, lat: float, lon: float) -> dict[str, Any] | None:
    params = {
        "SERVICE": "WMS", "REQUEST": "GetTimeseries", "LAYERS": layer,
        "QUERY_LAYERS": layer, "BBOX": f"{lon},{lat},{lon},{lat}",
        "SRS": "CRS:84", "FEATURE_COUNT": 5, "HEIGHT": 1, "WIDTH": 1,
        "X": 0, "Y": 0, "ELEVATION": 0, "VERSION": "1.1.1",
        "INFO_FORMAT": "text/csv",
    }
    response = _HTTP.get(product_url, params=params, timeout=20)
    response.raise_for_status()
    rows = list(csv.reader(io.StringIO(response.text)))
    header = next((i for i, row in enumerate(rows) if row and "time" in row[0].lower()), None)
    if header is None:
        return None
    parsed = []
    for row in rows[header + 1:]:
        if len(row) < 2:
            continue
        try:
            stamp = datetime.fromisoformat(row[0].strip().replace("Z", "+00:00"))
            numeric = next(float(part) for part in reversed(row[1:]) if part.strip())
            if numeric == numeric and abs(numeric) < 1e20:
                parsed.append((stamp, numeric))
        except (ValueError, StopIteration):
            continue
    now = datetime.now(timezone.utc)
    available = [item for item in parsed if item[0].astimezone(timezone.utc) <= now]
    selected = max(available or parsed, key=lambda item: item[0], default=None)
    if selected is None:
        return None
    return {"value": selected[1], "time": selected[0].isoformat()}


def _environment_readings(lat: float, lon: float) -> dict[str, Any]:
    thredds = "https://iioe-2.incois.gov.in/thredds/wms/osf"
    readings: dict[str, Any] = {}
    errors: list[str] = []
    try:
        products = _current_product_files()
        jobs = {
            "sst": (f"{thredds}/winds/{products['sst']}", "SST", "°C", "INCOIS OSF model forecast"),
            "current": (f"{thredds}/currents/{products['currents']}", "CURRENT", "m/s", "INCOIS OSF model forecast"),
            "mld": (f"{thredds}/winds/{products['mld']}", "MLD", "m", "INCOIS OSF model forecast"),
            "d20": (f"{thredds}/winds/{products['mld']}", "D20", "m", "INCOIS OSF model forecast"),
            "wind": (f"{thredds}/ww3/{products['waves']}", "UWND:VWND-mag", "m/s", "INCOIS OSF forecast"),
            "wave_height": (f"{thredds}/ww3/{products['waves']}", "HS", "m", "INCOIS OSF forecast"),
            "wave_period": (f"{thredds}/ww3/{products['waves']}", "T02", "s", "INCOIS OSF forecast"),
        }
        with ThreadPoolExecutor(max_workers=7) as pool:
            futures = {
                key: pool.submit(_read_timeseries, url, layer, lat, lon)
                for key, (url, layer, _, _) in jobs.items()
            }
            for key, future in futures.items():
                _, _, unit, source = jobs[key]
                try:
                    reading = future.result()
                    if reading is None:
                        errors.append(f"{key}: no value at this location")
                        continue
                    reading["unit"] = unit
                    reading["source"] = source
                    readings[key] = reading
                except Exception as exc:
                    logger.warning("INCOIS %s query failed: %s", key, exc)
                    errors.append(f"{key}: source temporarily unavailable")
    except Exception as exc:
        logger.warning("INCOIS OSF products could not be discovered: %s", exc)
        errors.append("INCOIS OSF forecast service temporarily unavailable")

    # The public ABIS page publishes the daily satellite products as mapped
    # imagery and a NetCDF download. It currently does not expose a supported
    # point-query API; do not turn a color on the image into a fake number.
    abis: dict[str, Any] = {"value": None, "unit": "mg/m³", "source": "INCOIS ABIS daily satellite product"}
    try:
        page = _HTTP.get(INCOIS_ABIS_PAGE, timeout=20)
        page.raise_for_status()
        match = re.search(r"(?:href|src)=['\"]([^'\"]*A-[^'\"]*-4KM-IndiaSriLanka-CHL\.png)['\"]", page.text)
        if match:
            abis["image_url"] = urljoin(INCOIS_ABIS_PAGE, match.group(1))
            abis["source_url"] = INCOIS_ABIS_PAGE
            date_match = re.search(r"A-([A-Za-z]+\d{4})-d(\d{2})-4KM-IndiaSriLanka-CHL\.png", match.group(1))
            if date_match:
                try:
                    month = datetime.strptime(date_match.group(1), "%b%Y").strftime("%b %Y")
                    abis["date"] = f"{int(date_match.group(2))} {month}"
                except ValueError:
                    abis["date"] = match.group(1)
            abis["colorbar_url"] = urljoin(INCOIS_ABIS_PAGE, "/datasets/ecosystem/HAB/ColorBars/CHL_colorbar.png")
    except Exception as exc:
        logger.warning("INCOIS ABIS product lookup failed: %s", exc)
        errors.append("chlorophyll: INCOIS daily map lookup unavailable")
    return {
        "location": {"latitude": lat, "longitude": lon},
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "readings": {**readings, "chlorophyll_a": abis},
        "errors": errors,
        "note": "INCOIS OSF values are model forecast fields. Satellite chlorophyll is shown as the official daily map; no numeric point value is reported unless INCOIS exposes a verified point query.",
    }


@app.get("/api/environment/current", tags=["Environmental data"])
def get_environment_conditions(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Get current INCOIS point forecasts and latest ABIS chlorophyll product."""
    key = (round(lat, 4), round(lon, 4))
    now = datetime.now(timezone.utc).timestamp()
    with _environment_cache_lock:
        cached = _environment_cache.get(key)
        if cached and now - cached[0] < 600:
            return cached[1]
    try:
        result = _environment_readings(lat, lon)
    except requests.RequestException as exc:
        logger.warning("INCOIS environment service unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="INCOIS environmental data service is temporarily unavailable. Try again shortly.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    with _environment_cache_lock:
        _environment_cache[key] = (now, result)
    return result


# Mount static frontend application
FRONTEND_DIR = ROOT_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

