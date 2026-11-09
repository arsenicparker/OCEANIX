"""OCEANIX Data Preparation & Alignment Pipeline.

Performs deterministic ingestion, cleaning, range validation, coordinate conversion,
and chronological split tagging according to Project Blueprint Section 8, 9, and 10.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from oceanix.data.audit import dms_to_dd

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("oceanix.data.prepare")

# Environmental feature list
ENV_FEATURE_COLUMNS = [
    "ph",
    "nppv",
    "phyc",
    "chl",
    "o2",
    "so",
    "mlotst",
    "uo",
    "vo",
    "thetao",
    "bottomT",
    "zos",
]


def prepare_incois_karnataka_pfz(
    raw_file: str | Path,
    output_dir: str | Path,
) -> pd.DataFrame:
    """Parse, clean, and validate INCOIS Karnataka PFZ advisory spreadsheet.

    Extracts operational advisory records, parses distance and depth ranges,
    converts DMS coordinates to decimal degrees, validates bounds, and outputs
    both CSV and GeoJSON for downstream mapping and verification.
    """
    raw_path = Path(raw_file)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Ingesting raw INCOIS PFZ advisory from %s...", raw_path)
    df_raw = pd.read_excel(raw_path)
    logger.info("Raw spreadsheet rows: %d, columns: %d", len(df_raw), len(df_raw.columns))

    # The tabular header is at row index 2
    raw_columns = [str(c).strip() for c in df_raw.iloc[2].values]
    df_data = df_raw.iloc[3:27].copy()
    df_data.columns = raw_columns

    records: List[Dict[str, Any]] = []
    for idx, row in df_data.iterrows():
        dist_str = str(row["Distance (km) From-To"]).strip()
        dist_parts = [float(x.strip()) for x in dist_str.split("-")]

        depth_str = str(row["Depth (mtr) From-To"]).strip()
        depth_parts = [float(x.strip()) for x in depth_str.split("-")]

        lat_dms = str(row["Latitude (dms)"]).strip()
        lon_dms = str(row["Longitude (dms)"]).strip()

        lat_dd = dms_to_dd(lat_dms)
        lon_dd = dms_to_dd(lon_dms)

        # Range validation
        if not (13.0 <= lat_dd <= 15.0):
            raise ValueError(f"Karnataka latitude out of expected range: {lat_dd}")
        if not (73.0 <= lon_dd <= 75.0):
            raise ValueError(f"Karnataka longitude out of expected range: {lon_dd}")

        bearing = float(row["Bearing (deg)"])
        if not (0.0 <= bearing <= 360.0):
            raise ValueError(f"Bearing out of valid compass range: {bearing}")

        records.append({
            "advisory_id": f"INCOIS-KAR-20261004-{len(records) + 1:02d}",
            "landing_centre": str(row["From the coast of"]).strip(),
            "direction": str(row["Direction"]).strip(),
            "bearing_deg": bearing,
            "distance_min_km": dist_parts[0],
            "distance_max_km": dist_parts[1],
            "depth_min_m": depth_parts[0],
            "depth_max_m": depth_parts[1],
            "latitude_dms": lat_dms,
            "longitude_dms": lon_dms,
            "latitude": round(lat_dd, 6),
            "longitude": round(lon_dd, 6),
            "forecast_valid_from": "2026-10-04",
            "forecast_valid_to": "2026-10-05",
            "source": "INCOIS Operational PFZ Advisory",
        })

    clean_df = pd.DataFrame(records)
    csv_out = out_dir / "cleaned_incois_karnataka.csv"
    clean_df.to_csv(csv_out, index=False)
    logger.info("Saved cleaned INCOIS advisory table (%d rows) to %s", len(clean_df), csv_out)

    # Generate GeoJSON feature collection for Leaflet map integration
    geojson_features = []
    for _, r in clean_df.iterrows():
        feat = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [r["longitude"], r["latitude"]],
            },
            "properties": {
                "advisory_id": r["advisory_id"],
                "landing_centre": r["landing_centre"],
                "direction": r["direction"],
                "bearing_deg": r["bearing_deg"],
                "distance_km": f"{r['distance_min_km']}-{r['distance_max_km']}",
                "depth_m": f"{r['depth_min_m']}-{r['depth_max_m']}",
                "forecast_valid_from": r["forecast_valid_from"],
                "forecast_valid_to": r["forecast_valid_to"],
                "source": r["source"],
            },
        }
        geojson_features.append(feat)

    geojson_doc = {
        "type": "FeatureCollection",
        "name": "INCOIS_Karnataka_PFZ_Advisory",
        "features": geojson_features,
    }
    geojson_out = out_dir / "cleaned_incois_karnataka.geojson"
    with open(geojson_out, "w", encoding="utf-8") as f:
        json.dump(geojson_doc, f, indent=2)
    logger.info("Saved GeoJSON advisory features to %s", geojson_out)

    return clean_df


def prepare_noaa_wio_dataset(
    raw_dir: str | Path,
    output_dir: str | Path,
    train_end_year: int = 2015,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean, align, and split NOAA Accession 0306675 fishery and oceanographic time-series.

    Merges catch observations with Copernicus Marine features, discards unobserved
    projection cells without target values, validates all physical/biological ranges,
    creates explicit date stamps, and marks chronological train vs holdout test splits.
    """
    raw_path = Path(raw_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    catch_file = raw_path / "Catch_data.txt"
    env_file = raw_path / "Environmental_data.txt"

    logger.info("Reading raw Catch data from %s...", catch_file)
    df_catch = pd.read_csv(catch_file, sep=r"\s+", quotechar='"')
    initial_catch_rows = len(df_catch)

    logger.info("Reading raw Environmental data from %s...", env_file)
    df_env = pd.read_csv(env_file, sep=r"\s+", quotechar='"')
    initial_env_rows = len(df_env)

    # Filter out unobserved projection grid cells where SKJ is NaN
    # (strictly adheres to Blueprint line 329: "Do not impute a missing target. Remove rows without valid target evidence.")
    df_observed_catch = df_catch[df_catch["SKJ"].notnull()].copy()
    observed_catch_rows = len(df_observed_catch)
    excluded_null_target_rows = initial_catch_rows - observed_catch_rows
    logger.info(
        "Extracted %d observed catch records; excluded %d unobserved background grid cells.",
        observed_catch_rows,
        excluded_null_target_rows,
    )

    # Perform deterministic inner join on composite space-time key
    join_keys = ["ID", "Lon", "Lat", "month", "year"]
    merged = pd.merge(df_observed_catch, df_env, on=join_keys, how="inner")
    joined_rows = len(merged)
    logger.info("Merged fishery and environmental records: %d rows (100%% match).", joined_rows)
    if joined_rows != observed_catch_rows:
        raise ValueError(
            f"Join mismatch: observed catch {observed_catch_rows} vs merged {joined_rows}"
        )

    # Standardize column naming
    rename_map = {
        "ID": "observation_id",
        "Lon": "longitude",
        "Lat": "latitude",
        "SKJ": "skipjack_catch_biomass",
    }
    merged = merged.rename(columns=rename_map)

    # Date creation (explicit YYYY-MM-01 format, preserving monthly grain)
    merged["observation_date"] = merged.apply(
        lambda r: f"{int(r['year']):04d}-{int(r['month']):02d}-01",
        axis=1,
    )

    # Range and domain validations
    assert (merged["longitude"] >= 38.0).all() and (merged["longitude"] <= 80.0).all(), "Longitude out of range"
    assert (merged["latitude"] >= -15.0).all() and (merged["latitude"] <= 15.0).all(), "Latitude out of range"
    assert (merged["month"] >= 1).all() and (merged["month"] <= 12).all(), "Month out of range"
    assert (merged["year"] >= 2005).all() and (merged["year"] <= 2019).all(), "Year out of range"
    assert (merged["skipjack_catch_biomass"] > 0).all(), "Catch biomass must be positive"

    # Chronological Holdout Split (Blueprint Section 10)
    # Train: 2005–2015 (11 years)
    # Frozen Holdout Test: 2016–2019 (4 years)
    merged["split"] = np.where(merged["year"] <= train_end_year, "train", "test")

    train_count = int((merged["split"] == "train").sum())
    test_count = int((merged["split"] == "test").sum())
    total_count = len(merged)

    logger.info(
        "Chronological split applied (cutoff year <= %d): Train = %d (%.1f%%), Test = %d (%.1f%%)",
        train_end_year,
        train_count,
        (train_count / total_count) * 100,
        test_count,
        (test_count / total_count) * 100,
    )

    # Organize clean columns
    ordered_columns = [
        "observation_id",
        "observation_date",
        "year",
        "month",
        "longitude",
        "latitude",
        "skipjack_catch_biomass",
        "split",
    ] + ENV_FEATURE_COLUMNS

    clean_df = merged[ordered_columns].copy()

    # Save processed CSV
    csv_out = out_dir / "clean_fishery_env.csv"
    clean_df.to_csv(csv_out, index=False)
    logger.info("Saved processed clean dataset to %s", csv_out)

    # Compile split metadata and preprocessing audit summary
    split_meta = {
        "dataset_name": "NOAA Accession 0306675 Clean Fishery-Environment Table",
        "total_records": total_count,
        "raw_catch_rows": initial_catch_rows,
        "raw_env_rows": initial_env_rows,
        "unobserved_grid_projection_cells_excluded": excluded_null_target_rows,
        "matched_observed_records": joined_rows,
        "train_end_year": train_end_year,
        "splits": {
            "train": {
                "count": train_count,
                "percentage": round((train_count / total_count) * 100, 2),
                "years": [int(y) for y in sorted(clean_df[clean_df["split"] == "train"]["year"].unique())],
                "date_range": [
                    str(clean_df[clean_df["split"] == "train"]["observation_date"].min()),
                    str(clean_df[clean_df["split"] == "train"]["observation_date"].max()),
                ],
            },
            "test": {
                "count": test_count,
                "percentage": round((test_count / total_count) * 100, 2),
                "years": [int(y) for y in sorted(clean_df[clean_df["split"] == "test"]["year"].unique())],
                "date_range": [
                    str(clean_df[clean_df["split"] == "test"]["observation_date"].min()),
                    str(clean_df[clean_df["split"] == "test"]["observation_date"].max()),
                ],
            },
        },
        "target_summary": {
            "target_field": "skipjack_catch_biomass",
            "unit": "Metric Tons (MT)",
            "min": float(clean_df["skipjack_catch_biomass"].min()),
            "median": float(clean_df["skipjack_catch_biomass"].median()),
            "mean": float(clean_df["skipjack_catch_biomass"].mean()),
            "max": float(clean_df["skipjack_catch_biomass"].max()),
            "std": float(clean_df["skipjack_catch_biomass"].std()),
        },
        "feature_missingness_by_split": {
            "train": clean_df[clean_df["split"] == "train"][ENV_FEATURE_COLUMNS].isnull().sum().to_dict(),
            "test": clean_df[clean_df["split"] == "test"][ENV_FEATURE_COLUMNS].isnull().sum().to_dict(),
        },
    }

    meta_out = out_dir / "split_metadata.json"
    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(split_meta, f, indent=2)
    logger.info("Saved split metadata and preprocessing audit to %s", meta_out)

    return clean_df, split_meta


def main() -> None:
    """Command-line interface to execute the full data preparation pipeline."""
    parser = argparse.ArgumentParser(description="OCEANIX Data Preparation Pipeline")
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Path to raw data directory (default: data/raw)",
    )
    parser.add_argument(
        "--interim-dir",
        default="data/interim",
        help="Path to interim data directory (default: data/interim)",
    )
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Path to processed data directory (default: data/processed)",
    )
    parser.add_argument(
        "--train-end-year",
        type=int,
        default=2015,
        help="Latest year included in the training split (default: 2015)",
    )
    args = parser.parse_args()

    raw_path = Path(args.raw_dir)
    interim_path = Path(args.interim_dir)
    processed_path = Path(args.processed_dir)

    print("\n" + "=" * 70)
    print("STARTING OCEANIX DATA PREPARATION PIPELINE (MILESTONE M2)")
    print("=" * 70)

    # 1. Process Route A: INCOIS Karnataka Advisory
    pfz_file = raw_path / "PfzForecast_KARNATAKA.xls"
    if pfz_file.exists():
        prepare_incois_karnataka_pfz(pfz_file, interim_path)
    else:
        logger.warning("INCOIS PFZ file %s not found. Skipping Route A.", pfz_file)

    # 2. Process Route B: NOAA WIO Catch & Copernicus Environmental dataset
    prepare_noaa_wio_dataset(
        raw_path,
        processed_path,
        train_end_year=args.train_end_year,
    )

    print("=" * 70)
    print("OCEANIX DATA PREPARATION COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
