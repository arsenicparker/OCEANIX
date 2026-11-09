"""Unit tests for OCEANIX dataset audit and data preparation checks."""

import json
from pathlib import Path
import pytest
import pandas as pd
from oceanix.data.audit import (
    compute_sha256,
    dms_to_dd,
    audit_incois_karnataka_pfz,
    audit_noaa_0306675,
)
from oceanix.data.prepare import (
    prepare_incois_karnataka_pfz,
    prepare_noaa_wio_dataset,
    ENV_FEATURE_COLUMNS,
)

RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
PROCESSED_DIR = Path("data/processed")

EXPECTED_PFZ_SHA = "2d532086e0601a9875fb32ebc435844c5c4c8e6fc1c91b1f8dc3f6871d436378"
EXPECTED_CATCH_SHA = "4f9e4cdd8d8c65d55ef5c5fb460a43b3ea3cd35cecd2b00f305f576bc3da317c"
EXPECTED_ENV_SHA = "0613e8aeef0d9ee9ddf42634712341b7f312930ca5c21275e2affdbf1b61082a"


def test_dms_to_dd_conversion():
    """Verify DMS to Decimal Degrees conversion for standard cardinal directions."""
    # North
    assert pytest.approx(dms_to_dd("14 43 18 N"), rel=1e-5) == 14.721667
    # East
    assert pytest.approx(dms_to_dd("73 37 15 E"), rel=1e-5) == 73.620833
    # South (negative)
    assert pytest.approx(dms_to_dd("10 30 00 S"), rel=1e-5) == -10.500000
    # West (negative)
    assert pytest.approx(dms_to_dd("45 15 00 W"), rel=1e-5) == -45.250000


def test_dms_to_dd_invalid():
    """Verify malformed DMS raises ValueError."""
    with pytest.raises(ValueError):
        dms_to_dd("invalid coordinate")


def test_raw_files_exist():
    """Ensure all required raw data files are in place."""
    assert (RAW_DIR / "PfzForecast_KARNATAKA.xls").exists()
    assert (RAW_DIR / "Catch_data.txt").exists()
    assert (RAW_DIR / "Environmental_data.txt").exists()


def test_raw_checksums():
    """Ensure raw files have not been modified or corrupted."""
    pfz_sha = compute_sha256(RAW_DIR / "PfzForecast_KARNATAKA.xls")
    catch_sha = compute_sha256(RAW_DIR / "Catch_data.txt")
    env_sha = compute_sha256(RAW_DIR / "Environmental_data.txt")

    assert pfz_sha == EXPECTED_PFZ_SHA
    assert catch_sha == EXPECTED_CATCH_SHA
    assert env_sha == EXPECTED_ENV_SHA


def test_incois_audit_parsing():
    """Verify INCOIS Karnataka advisory parsing extracts exactly 24 valid records."""
    audit = audit_incois_karnataka_pfz(RAW_DIR / "PfzForecast_KARNATAKA.xls")
    assert audit["status"] == "PRESENT"
    assert audit["advisory_point_count"] == 24
    bounds = audit["geographic_bounds"]
    assert 13.0 <= bounds["lat_min"] <= bounds["lat_max"] <= 15.0
    assert 73.0 <= bounds["lon_min"] <= bounds["lon_max"] <= 75.0


def test_noaa_audit_join_integrity():
    """Verify NOAA 0306675 join integrity between catch and environmental series."""
    audit = audit_noaa_0306675(RAW_DIR)
    assert audit["status"] == "PRESENT"
    join_info = audit["join_integrity"]
    assert join_info["alignment_pass"] is True
    assert join_info["unmatched_rows"] == 0
    assert join_info["inner_join_matches"] == 66520
    assert audit["target_analysis"]["observed_records"] == 19866


def test_prepare_incois_pfz(tmp_path):
    """Test deterministic preparation of INCOIS Karnataka advisory."""
    clean_df = prepare_incois_karnataka_pfz(
        RAW_DIR / "PfzForecast_KARNATAKA.xls",
        tmp_path,
    )
    assert len(clean_df) == 24
    expected_cols = [
        "advisory_id", "landing_centre", "direction", "bearing_deg",
        "distance_min_km", "distance_max_km", "depth_min_m", "depth_max_m",
        "latitude_dms", "longitude_dms", "latitude", "longitude",
        "forecast_valid_from", "forecast_valid_to", "source",
    ]
    for col in expected_cols:
        assert col in clean_df.columns

    # Verify GeoJSON output
    geojson_file = tmp_path / "cleaned_incois_karnataka.geojson"
    assert geojson_file.exists()
    with open(geojson_file, "r", encoding="utf-8") as f:
        geo_data = json.load(f)
    assert geo_data["type"] == "FeatureCollection"
    assert len(geo_data["features"]) == 24


def test_prepare_noaa_wio(tmp_path):
    """Test deterministic preparation and splitting of NOAA WIO dataset."""
    clean_df, meta = prepare_noaa_wio_dataset(
        RAW_DIR,
        tmp_path,
        train_end_year=2015,
    )
    assert len(clean_df) == 19866
    assert meta["unobserved_grid_projection_cells_excluded"] == 46654
    assert meta["splits"]["train"]["count"] == 13599
    assert meta["splits"]["test"]["count"] == 6267

    # Check zero target missingness
    assert clean_df["skipjack_catch_biomass"].isnull().sum() == 0
    assert (clean_df["skipjack_catch_biomass"] > 0).all()

    # Check all environmental feature columns exist
    for col in ENV_FEATURE_COLUMNS:
        assert col in clean_df.columns

    # Check temporal split isolation (no leakage across cut)
    train_years = set(clean_df[clean_df["split"] == "train"]["year"].unique())
    test_years = set(clean_df[clean_df["split"] == "test"]["year"].unique())
    assert train_years.isdisjoint(test_years)
    assert max(train_years) == 2015
    assert min(test_years) == 2016
