"""Unit tests for OCEANIX dataset audit and integrity checks."""

from pathlib import Path
import pytest
import pandas as pd
from oceanix.data.audit import (
    compute_sha256,
    dms_to_dd,
    audit_incois_karnataka_pfz,
    audit_noaa_0306675,
)

RAW_DIR = Path("data/raw")
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
