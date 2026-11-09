"""Integration tests for OCEANIX FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from oceanix.api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify /health returns status ok and model is loaded."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert "model_version" in data


def test_model_info_endpoint():
    """Verify /model-info returns complete schema, metrics, and limitations."""
    response = client.get("/model-info")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "OCEANIX Skipjack Tuna Suitability Regressor"
    assert data["target_variable"] == "skipjack_catch_biomass"
    assert "features" in data
    assert len(data["features"]) == 15
    assert "metrics_held_out_test_set" in data
    assert "limitations" in data
    assert len(data["limitations"]) > 0


def test_predict_success_minimal_input():
    """Verify /predict succeeds with minimal required coordinates and month."""
    payload = {
        "longitude": 52.25,
        "latitude": -2.25,
        "month": 7,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["target"] == "skipjack_catch_biomass"
    assert isinstance(data["predicted_catch_biomass_mt"], (int, float))
    assert data["predicted_catch_biomass_mt"] >= 0.0
    assert data["suitability_tier"] in [
        "Low Suitability",
        "Moderate Suitability",
        "High Suitability",
    ]
    assert "disclaimer" in data


def test_predict_success_full_features():
    """Verify /predict succeeds when all oceanographic features are provided."""
    payload = {
        "longitude": 55.25,
        "latitude": 4.75,
        "month": 1,
        "thetao": 26.78,
        "chl": 0.34,
        "so": 35.42,
        "o2": 207.54,
        "mlotst": 23.08,
        "uo": -0.19,
        "vo": 0.10,
        "ph": 8.04,
        "zos": 0.23,
        "bottomT": 0.88,
        "phyc": 1.79,
        "nppv": 23.88,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["predicted_catch_biomass_mt"] >= 0.0


def test_predict_invalid_latitude():
    """Verify 422 is returned when latitude exceeds the Western Indian Ocean domain."""
    payload = {
        "longitude": 52.25,
        "latitude": 35.0,  # Valid WIO is -15 to +15
        "month": 6,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_invalid_longitude():
    """Verify 422 is returned when longitude exceeds the Western Indian Ocean domain."""
    payload = {
        "longitude": 105.0,  # Valid WIO is 38 to 80
        "latitude": 0.0,
        "month": 6,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_invalid_month():
    """Verify 422 is returned for invalid month number."""
    payload = {
        "longitude": 52.25,
        "latitude": -2.25,
        "month": 13,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_missing_body():
    """Verify 422 on empty or missing body."""
    response = client.post("/predict", json={})
    assert response.status_code == 422


def test_karnataka_advisories_endpoint():
    """Verify /advisories/karnataka returns valid GeoJSON FeatureCollection."""
    response = client.get("/advisories/karnataka")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 24
    for feat in data["features"]:
        assert feat["geometry"]["type"] == "Point"
        assert len(feat["geometry"]["coordinates"]) == 2
        assert "advisory_id" in feat["properties"]


def test_frontend_index_served():
    """Verify that root endpoint serves the HTML frontend."""
    response = client.get("/")
    assert response.status_code == 200
    assert "OCEANIX" in response.text
    assert "leafletMap" in response.text
