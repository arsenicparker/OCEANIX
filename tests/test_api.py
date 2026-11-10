"""API-handler checks for the INCOIS data playground.

The managed Windows test sandbox blocks the socketpair used by Starlette's
TestClient, so these tests exercise handlers and static assets directly.
"""

import json
from pathlib import Path

from oceanix.api.main import (
    app,
    get_current_pfz_snapshot,
    get_current_pfz_summary,
    get_karnataka_advisories,
    health_check,
)


def test_health_endpoint_reports_prepared_snapshot():
    data = health_check().model_dump()
    assert data["status"] == "ok"
    assert data["data_loaded"] is True
    assert data["snapshot_date"] == "2026-11-09"


def test_current_pfz_snapshot_geojson():
    data = json.loads(get_current_pfz_snapshot().body)
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 522
    for feature in data["features"]:
        assert feature["geometry"]["type"] == "Point"
        assert len(feature["geometry"]["coordinates"]) == 2
        assert feature["properties"]["sector_name"]
        assert feature["properties"]["forecast_valid_to"] == "2026-11-10"


def test_current_pfz_summary():
    data = get_current_pfz_summary()
    assert data["point_count"] == 522
    assert data["sector_count"] == 14
    assert data["is_live_connection"] is False
    assert data["coordinate_format"] == "DMS (higher precision)"


def test_archived_karnataka_advisory_endpoint_remains_available():
    data = json.loads(get_karnataka_advisories().body)
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 24


def test_manual_measurement_prediction_is_not_exposed():
    route_paths = {getattr(route, "path", None) for route in app.routes}
    assert "/predict" not in route_paths


def test_frontend_and_static_assets_are_served():
    root = Path(__file__).resolve().parents[1]
    html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    app_js = (root / "frontend" / "js" / "app.js").read_text(encoding="utf-8")
    assert "OCEANIX" in html
    assert "leafletMap" in html
    assert "leaflet.heat" in html
    assert "catch probability" in html
    assert "tile.openstreetmap.org" in app_js
    assert "basemaps.cartocdn.com" not in app_js
