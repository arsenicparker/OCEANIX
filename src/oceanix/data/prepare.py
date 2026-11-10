"""OCEANIX Data Preparation & Alignment Pipeline.

Performs deterministic ingestion, cleaning, range validation, coordinate conversion,
and chronological split tagging according to Project Blueprint Section 8, 9, and 10.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
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

INCOIS_SECTORS = {
    "SEC001": "Gujarat",
    "SEC002": "Maharashtra",
    "SEC003": "Goa",
    "SEC004": "Karnataka",
    "SEC005": "Kerala",
    "SEC006": "South Tamil Nadu",
    "SEC007": "North Tamil Nadu",
    "SEC008": "South Andhra Pradesh",
    "SEC009": "North Andhra Pradesh",
    "SEC010": "Odisha",
    "SEC011": "West Bengal",
    "SEC012": "Andaman",
    "SEC013": "Nicobar",
    "SEC014": "Lakshadweep",
}


def _parse_incois_coordinate(value: Any) -> float:
    """Parse INCOIS coordinates in either DMS or decimal-degree form."""
    text = str(value).strip().upper()
    if not text or text == "NAN":
        raise ValueError("Empty INCOIS coordinate")
    direction = text[-1] if text[-1] in {"N", "S", "E", "W"} else None
    coordinate_text = text[:-1].strip() if direction else text
    parts = coordinate_text.split()
    if len(parts) >= 3:
        result = dms_to_dd(text)
    else:
        result = float(parts[0])
        if direction in {"S", "W"}:
            result = -abs(result)
        elif direction in {"N", "E"}:
            result = abs(result)
    return result


def _find_incois_header(df_raw: pd.DataFrame) -> int:
    """Find the table header row across INCOIS spreadsheet export variants."""
    for index, row in df_raw.iterrows():
        if any(str(value).strip().lower() == "from the coast of" for value in row):
            return int(index)
    raise ValueError("Could not find the INCOIS PFZ table header")


def prepare_incois_current_snapshot(
    raw_dir: str | Path,
    output_dir: str | Path,
    manifest_path: str | Path | None = None,
) -> pd.DataFrame:
    """Combine dated official INCOIS sector exports into validated CSV and GeoJSON.

    The snapshot export files are source artifacts and remain unchanged. This
    parser supports both DMS and decimal-degree coordinates and skips spreadsheet
    footer text rather than treating it as an advisory record.
    """
    raw_path = Path(raw_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, Any] = {}
    if manifest_path and Path(manifest_path).exists():
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8-sig"))
    manifest_sectors = {
        item.get("sector"): item for item in manifest.get("sectors", [])
    }

    records: List[Dict[str, Any]] = []
    discovered = sorted(raw_path.glob("INCOIS_PFZ_SEC*_*.xls"))
    dated_files = [
        path for path in discovered
        if re.search(r"(SEC\d{3})_(\d{4}-\d{2}-\d{2})\.xls$", path.name)
    ]
    manifest_date = manifest.get("retrieved_local_date")
    if manifest_date:
        files = [path for path in dated_files if path.name.endswith(f"_{manifest_date}.xls")]
    else:
        latest_date = max(
            re.search(r"(\d{4}-\d{2}-\d{2})\.xls$", path.name).group(1)
            for path in dated_files
        )
        files = [path for path in dated_files if path.name.endswith(f"_{latest_date}.xls")]
    if not files:
        raise FileNotFoundError(f"No dated INCOIS sector exports found in {raw_path}")

    for source_path in files:
        match = re.search(r"(SEC\d{3})_(\d{4}-\d{2}-\d{2})\.xls$", source_path.name)
        if not match:
            continue
        sector_code, snapshot_date = match.groups()
        if sector_code not in INCOIS_SECTORS:
            continue

        df_raw = pd.read_excel(source_path, header=None)
        header_index = _find_incois_header(df_raw)
        columns = [str(value).strip().replace("\n", " ") for value in df_raw.iloc[header_index]]
        data = df_raw.iloc[header_index + 1 :].copy()
        data.columns = columns

        header_text = " ".join(
            str(value) for value in df_raw.iloc[:header_index].values.flatten() if pd.notna(value)
        )
        validity = re.search(
            r"FORECAST\s+VALIDITY\s+FROM\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+TO\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})",
            header_text,
            flags=re.IGNORECASE,
        )
        valid_from = pd.to_datetime(validity.group(1), format="%d %b %Y").date().isoformat() if validity else snapshot_date
        valid_to = pd.to_datetime(validity.group(2), format="%d %b %Y").date().isoformat() if validity else None
        source_meta = manifest_sectors.get(sector_code, {})

        for _, row in data.iterrows():
            landing = row.get("From the coast of")
            if pd.isna(landing):
                continue
            try:
                bearing = float(row.get("Bearing (deg)"))
                distance_parts = [float(part.strip()) for part in str(row.get("Distance (km) From-To")).split("-")]
                depth_parts = [float(part.strip()) for part in str(row.get("Depth (mtr) From-To")).split("-")]
                latitude = _parse_incois_coordinate(row.get("Latitude (dms)", row.get("Latitude (dd)")))
                longitude = _parse_incois_coordinate(row.get("Longitude (dms)", row.get("Longitude (dd)")))
            except (TypeError, ValueError, KeyError):
                # Spreadsheet footer rows can occupy the same columns as records.
                continue

            if not 0 <= bearing <= 360:
                raise ValueError(f"Invalid bearing in {source_path.name}: {bearing}")
            if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                raise ValueError(f"Invalid coordinates in {source_path.name}: {latitude}, {longitude}")

            records.append(
                {
                    "advisory_id": f"INCOIS-{sector_code}-{snapshot_date}-{len(records) + 1:04d}",
                    "sector_code": sector_code,
                    "sector_name": INCOIS_SECTORS[sector_code],
                    "landing_centre": str(landing).strip(),
                    "direction": str(row.get("Direction", "")).strip(),
                    "bearing_deg": bearing,
                    "distance_min_km": distance_parts[0],
                    "distance_max_km": distance_parts[1],
                    "depth_min_m": depth_parts[0],
                    "depth_max_m": depth_parts[1],
                    "latitude_raw": str(row.get("Latitude (dms)", row.get("Latitude (dd)", ""))).strip(),
                    "longitude_raw": str(row.get("Longitude (dms)", row.get("Longitude (dd)", ""))).strip(),
                    "latitude": round(latitude, 6),
                    "longitude": round(longitude, 6),
                    "snapshot_date": snapshot_date,
                    "forecast_valid_from": valid_from,
                    "forecast_valid_to": valid_to,
                    "source_updated_at": source_meta.get("updated"),
                    "source_file": source_path.name,
                    "source": "INCOIS Potential Fishing Zone Advisory",
                }
            )

    clean_df = pd.DataFrame(records)
    if clean_df.empty:
        raise ValueError("No valid INCOIS PFZ records were parsed from the snapshot files")
    clean_df = clean_df.drop_duplicates(subset=["sector_code", "landing_centre", "latitude", "longitude"])
    clean_df.to_csv(out_dir / "incois_current_pfz.csv", index=False)

    features = []
    for record in clean_df.to_dict(orient="records"):
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [record["longitude"], record["latitude"]]},
                "properties": {key: value for key, value in record.items() if key not in {"longitude", "latitude"}},
            }
        )
    geojson = {
        "type": "FeatureCollection",
        "name": "INCOIS_Current_PFZ_Snapshot",
        "features": features,
        "metadata": {
            "snapshot_date": manifest.get("retrieved_local_date"),
            "source": manifest.get("source", "https://www.incois.gov.in/MarineFisheries/PfzAdvisory"),
            "note": "A dated snapshot of official PFZ advisory locations; not a model prediction.",
        },
    }
    (out_dir / "incois_current_pfz.geojson").write_text(
        json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("Prepared %d current INCOIS advisory points from %d sector exports", len(clean_df), len(files))
    return clean_df


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
