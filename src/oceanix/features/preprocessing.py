"""OCEANIX Feature Preprocessing Pipelines.

Provides scikit-learn ColumnTransformer configurations for tabular imputation
and feature schema management according to Blueprint Section 9.
"""

from __future__ import annotations

from typing import List
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

# Spatial and temporal coordinate features
SPATIAL_TEMPORAL_FEATURES: List[str] = [
    "longitude",
    "latitude",
    "month",
]

# Physical and biogeochemical oceanographic predictors
OCEANOGRAPHIC_FEATURES: List[str] = [
    "thetao",   # Sea surface potential temperature (SST) in deg C
    "chl",      # Chlorophyll-a mass concentration in mg/m3
    "so",       # Sea surface salinity in PSU
    "o2",       # Dissolved oxygen concentration in mmol/m3
    "mlotst",   # Mixed layer depth in meters
    "uo",       # Eastward sea water current velocity in m/s
    "vo",       # Northward sea water current velocity in m/s
    "ph",       # Sea surface pH
    "zos",      # Sea surface height above geoid in meters
    "bottomT",  # Bottom temperature in deg C
    "phyc",     # Phytoplankton carbon in mmol/m3
    "nppv",     # Net primary production in mg C / m3 / day
]

# Complete model predictor feature set
ALL_PREDICTOR_FEATURES: List[str] = SPATIAL_TEMPORAL_FEATURES + OCEANOGRAPHIC_FEATURES


def get_feature_preprocessor(
    features: List[str] | None = None,
    impute_strategy: str = "median",
) -> ColumnTransformer:
    """Build a deterministic ColumnTransformer for numeric imputation.

    Parameters
    ----------
    features : list of str, optional
        Features to include. Defaults to ALL_PREDICTOR_FEATURES.
    impute_strategy : str, default='median'
        Strategy for missing value imputation.

    Returns
    -------
    ColumnTransformer
        Fitted or unfitted transformer ready for inclusion in a scikit-learn Pipeline.
    """
    if features is None:
        features = ALL_PREDICTOR_FEATURES

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy=impute_strategy)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_transformer, features),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return preprocessor

