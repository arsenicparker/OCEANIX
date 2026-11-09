"""FastAPI application for OCEANIX Marine Intelligence Service.

Serves model predictions, metadata, and operational advisory overlays in adherence
with Project Blueprint Section 12, 13, and Implementation Plan M5.
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import pandas as pd
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from oceanix.api.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
)
from oceanix.features.preprocessing import ALL_PREDICTOR_FEATURES

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("oceanix.api")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_PATH = ROOT_DIR / "models" / "pipeline.joblib"
METADATA_PATH = ROOT_DIR / "models" / "model_metadata.json"
ADVISORY_GEOJSON_PATH = ROOT_DIR / "data" / "interim" / "cleaned_incois_karnataka.geojson"

# Global singleton model & metadata container
app_state: Dict[str, Any] = {
    "model": None,
    "metadata": None,
    "advisories_geojson": None,
}


def load_artifacts() -> None:
    """Load model pipeline, metadata, and advisory GeoJSON into global state."""
    # 1. Load trained scikit-learn pipeline
    if app_state.get("model") is None and MODEL_PATH.exists():
        try:
            app_state["model"] = joblib.load(MODEL_PATH)
            logger.info("Successfully loaded model pipeline artifact from %s", MODEL_PATH)
        except Exception as e:
            logger.error("Failed to load model pipeline artifact: %s", e)

    # 2. Load model metadata
    if app_state.get("metadata") is None and METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                app_state["metadata"] = json.load(f)
            logger.info("Loaded model metadata from %s", METADATA_PATH)
        except Exception as e:
            logger.error("Failed to load model metadata: %s", e)

    # 3. Load operational advisory GeoJSON
    if app_state.get("advisories_geojson") is None and ADVISORY_GEOJSON_PATH.exists():
        try:
            with open(ADVISORY_GEOJSON_PATH, "r", encoding="utf-8") as f:
                app_state["advisories_geojson"] = json.load(f)
            logger.info("Loaded INCOIS Karnataka advisory GeoJSON from %s", ADVISORY_GEOJSON_PATH)
        except Exception as e:
            logger.error("Failed to load advisory GeoJSON: %s", e)


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
    title="OCEANIX Marine Intelligence API",
    description=(
        "Decision-support API for marine environmental intelligence and "
        "fishing-zone suitability prediction based on historical oceanographic time-series."
    ),
    version="1.0.0",
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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    """Confirm API is operational and report loaded model status."""
    load_artifacts()
    model_loaded = app_state["model"] is not None
    version = (
        app_state["metadata"].get("model_version", "1.0.0")
        if app_state["metadata"]
        else "unknown"
    )
    return HealthResponse(
        status="ok",
        model_loaded=model_loaded,
        model_version=version,
    )


@app.get("/model-info", response_model=ModelInfoResponse, tags=["System"])
def get_model_info() -> ModelInfoResponse:
    """Explain supported target, region, feature schema, test metrics, and limitations."""
    load_artifacts()
    meta = app_state.get("metadata")
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model metadata is not loaded.",
        )
    return ModelInfoResponse(**meta)


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


@app.post("/predict", response_model=PredictionResponse, tags=["Inference"])
def predict_suitability(request: PredictionRequest) -> PredictionResponse:
    """Predict skipjack tuna suitability and estimated catch biomass for given coordinates and features."""
    load_artifacts()
    pipeline = app_state.get("model")
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model pipeline is not loaded on the server.",
        )

    # Convert request to DataFrame aligned to training feature names
    input_dict = request.model_dump()
    row_data = {feat: input_dict.get(feat, None) for feat in ALL_PREDICTOR_FEATURES}
    df_input = pd.DataFrame([row_data])

    try:
        raw_prediction = pipeline.predict(df_input)
        pred_val = float(max(0.0, raw_prediction[0]))
    except Exception as e:
        logger.error("Inference execution failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}",
        )

    # Determine suitability tier based on empirical quartiles
    # (p25 = 12.0 MT, median = 27.0 MT, p75 = 58.4 MT)
    if pred_val >= 45.0:
        tier = "High Suitability"
    elif pred_val >= 20.0:
        tier = "Moderate Suitability"
    else:
        tier = "Low Suitability"

    meta = app_state.get("metadata", {})
    return PredictionResponse(
        status="ok",
        model_name=meta.get("model_name", "OCEANIX Skipjack Tuna Suitability Regressor"),
        model_version=meta.get("model_version", "1.0.0"),
        target="skipjack_catch_biomass",
        predicted_catch_biomass_mt=round(pred_val, 2),
        suitability_tier=tier,
        study_region="Western Indian Ocean (WIO) [38.75°E - 79.75°E, -14.75°S - 14.75°N]",
        input_coordinates={
            "longitude": request.longitude,
            "latitude": request.latitude,
            "month": request.month,
        },
        disclaimer=(
            "Decision-support estimate based on historical 2005-2019 environmental time-series. "
            "Does not constitute official marine advice, sea navigation guidance, or a guarantee of fish catch."
        ),
    )


# Mount static frontend application
FRONTEND_DIR = ROOT_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

