"""The current prototype is a data explorer; model work is gated on historical INCOIS labels."""

from pathlib import Path

from oceanix.api.main import app


ROOT = Path(__file__).resolve().parents[1]


def test_current_app_does_not_claim_a_trained_incois_model():
    route_paths = {route.path for route in app.routes}
    assert "/predict" not in route_paths
    assert "/model-info" not in route_paths


def test_local_wio_artifact_is_not_connected_to_current_api():
    artifact = ROOT / "models" / "pipeline.joblib"
    if artifact.exists():
        import joblib

        legacy_pipeline = joblib.load(artifact)
        assert hasattr(legacy_pipeline, "predict")
    route_paths = {route.path for route in app.routes}
    assert "/api/pfz/current" in route_paths


def test_old_wio_dataset_is_kept_as_reference_not_current_app_input():
    assert (ROOT / "data" / "raw" / "Catch_data.txt").exists()
    assert (ROOT / "data" / "raw" / "Environmental_data.txt").exists()
    route_paths = {route.path for route in app.routes}
    assert "/api/pfz/current" in route_paths
