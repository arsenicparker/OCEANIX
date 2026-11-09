"""Smoke tests for OCEANIX trained model pipeline artifact."""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest

from oceanix.features.preprocessing import ALL_PREDICTOR_FEATURES

MODEL_PATH = Path("models/pipeline.joblib")
DATA_PATH = Path("data/processed/clean_fishery_env.csv")


def test_model_artifact_exists():
    """Verify that the trained pipeline artifact is serialized on disk."""
    assert MODEL_PATH.exists(), f"Model artifact missing at {MODEL_PATH}"


def test_model_loads_successfully():
    """Verify pipeline artifact can be loaded via joblib."""
    pipeline = joblib.load(MODEL_PATH)
    assert pipeline is not None
    assert hasattr(pipeline, "predict")
    assert "preprocessor" in pipeline.named_steps
    assert "model" in pipeline.named_steps


def test_single_inference_smoke():
    """Smoke test: execute inference on a single test record and verify valid output."""
    pipeline = joblib.load(MODEL_PATH)

    # Sample input dictionary representative of Western Indian Ocean
    sample_input = pd.DataFrame([{
        "longitude": 52.25,
        "latitude": -2.25,
        "month": 7,
        "thetao": 27.85,
        "chl": 0.14,
        "so": 35.42,
        "o2": 202.35,
        "mlotst": 18.5,
        "uo": -0.05,
        "vo": 0.03,
        "ph": 8.03,
        "zos": 0.36,
        "bottomT": 1.15,
        "phyc": 1.35,
        "nppv": 2.50,
    }])

    pred = pipeline.predict(sample_input)
    assert len(pred) == 1
    assert isinstance(pred[0], (float, np.floating))
    assert not np.isnan(pred[0])
    assert not np.isinf(pred[0])
    # Biomass predictions must be non-negative
    assert pred[0] >= 0.0


def test_batch_inference_on_processed_data():
    """Verify inference over a batch of records from the processed test partition."""
    pipeline = joblib.load(MODEL_PATH)
    df = pd.read_csv(DATA_PATH)
    test_samples = df[df["split"] == "test"].head(20)

    preds = pipeline.predict(test_samples[ALL_PREDICTOR_FEATURES])
    assert len(preds) == 20
    assert (preds >= 0.0).all()
    assert not np.isnan(preds).any()
