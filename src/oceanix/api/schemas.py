"""Pydantic schemas for OCEANIX FastAPI endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Input features required to predict skipjack tuna suitability."""

    longitude: float = Field(
        ...,
        ge=38.0,
        le=80.0,
        description="Longitude in decimal degrees (Western Indian Ocean domain: 38.0°E to 80.0°E)",
        examples=[52.25],
    )
    latitude: float = Field(
        ...,
        ge=-15.0,
        le=15.0,
        description="Latitude in decimal degrees (Western Indian Ocean domain: -15.0°S to 15.0°N)",
        examples=[-2.25],
    )
    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Calendar month of observation (1 to 12)",
        examples=[7],
    )
    thetao: Optional[float] = Field(
        default=None,
        ge=15.0,
        le=35.0,
        description="Sea Surface Potential Temperature (SST) in °C",
        examples=[27.85],
    )
    chl: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=50.0,
        description="Chlorophyll-a mass concentration in mg/m³",
        examples=[0.14],
    )
    so: Optional[float] = Field(
        default=None,
        ge=25.0,
        le=42.0,
        description="Sea Surface Salinity in PSU",
        examples=[35.42],
    )
    o2: Optional[float] = Field(
        default=None,
        ge=100.0,
        le=300.0,
        description="Dissolved Oxygen concentration in mmol/m³",
        examples=[202.35],
    )
    mlotst: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=200.0,
        description="Ocean Mixed Layer Depth (MLD) in meters",
        examples=[18.5],
    )
    uo: Optional[float] = Field(
        default=None,
        ge=-5.0,
        le=5.0,
        description="Eastward sea water current velocity in m/s",
        examples=[-0.05],
    )
    vo: Optional[float] = Field(
        default=None,
        ge=-5.0,
        le=5.0,
        description="Northward sea water current velocity in m/s",
        examples=[0.03],
    )
    ph: Optional[float] = Field(
        default=None,
        ge=7.0,
        le=9.0,
        description="Sea surface pH",
        examples=[8.03],
    )
    zos: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Sea surface height above geoid in meters",
        examples=[0.36],
    )
    bottomT: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=35.0,
        description="Sea water potential temperature at sea floor in °C",
        examples=[1.15],
    )
    phyc: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=20.0,
        description="Phytoplankton expressed as carbon in mmol/m³",
        examples=[1.35],
    )
    nppv: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Net primary production of biomass in mg C / m³ / day",
        examples=[2.50],
    )


class PredictionResponse(BaseModel):
    """Response containing prediction estimate, suitability tier, and limitations."""

    status: str = Field("ok", description="Status string")
    model_name: str = Field(..., description="Name of the fitted model")
    model_version: str = Field(..., description="Version of the model artifact")
    target: str = Field(..., description="Target variable name")
    predicted_catch_biomass_mt: float = Field(
        ...,
        description="Estimated skipjack tuna catch biomass in Metric Tons",
    )
    suitability_tier: str = Field(
        ...,
        description="Categorical suitability interpretation (Low / Moderate / High)",
    )
    study_region: str = Field(..., description="Geographical study boundaries")
    input_coordinates: Dict[str, float] = Field(..., description="Query coordinates")
    disclaimer: str = Field(
        ...,
        description="Public notice of limitations and non-guarantee of catch",
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field("ok", description="Service health status")
    model_loaded: bool = Field(..., description="Whether model artifact is loaded in memory")
    model_version: str = Field(..., description="Model version")


class ModelInfoResponse(BaseModel):
    """Model metadata and schema specification."""

    model_name: str
    model_version: str
    algorithm: str
    target_variable: str
    target_units: str
    study_area: str
    features: List[str]
    metrics_held_out_test_set: Dict[str, Any]
    feature_importances: List[Dict[str, Any]]
    limitations: List[str]
