"""OCEANIX Model Pipeline Construction & Evaluation.

Implements baseline estimator (DummyRegressor) and primary estimator (RandomForestRegressor
with log1p transformed target) in adherence with Blueprint Section 10 and 11.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from oceanix.features.preprocessing import (
    ALL_PREDICTOR_FEATURES,
    get_feature_preprocessor,
)

logger = logging.getLogger("oceanix.modeling.pipeline")


def build_baseline_pipeline(
    strategy: str = "median",
    features: List[str] | None = None,
) -> Pipeline:
    """Build a baseline DummyRegressor pipeline.

    Used as the required benchmark to establish a minimum performance floor.
    """
    preprocessor = get_feature_preprocessor(features=features)
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", DummyRegressor(strategy=strategy)),
        ]
    )
    return pipeline


def build_primary_pipeline(
    n_estimators: int = 100,
    max_depth: int = 12,
    min_samples_leaf: int = 5,
    random_state: int = 42,
    features: List[str] | None = None,
    n_jobs: int = 1,
) -> Pipeline:
    """Build the primary RandomForestRegressor pipeline with log1p target transformation.

    The log1p transformation handles the highly skewed positive catch biomass distribution
    while preserving non-negative output upon inverse transformation.
    """
    preprocessor = get_feature_preprocessor(features=features)
    base_rf = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=n_jobs,
    )

    transformed_regressor = TransformedTargetRegressor(
        regressor=base_rf,
        func=np.log1p,
        inverse_func=np.expm1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", transformed_regressor),
        ]
    )
    return pipeline


def evaluate_regressor(
    pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, float]:
    """Calculate standard regression metrics: MAE, RMSE, and R-squared."""
    y_pred = pipeline.predict(X_test)
    # Clip negative predictions if any floating point precision artifact occurs
    y_pred = np.clip(y_pred, a_min=0.0, a_max=None)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
    }


def extract_feature_importances(
    pipeline: Pipeline,
    feature_names: List[str],
) -> List[Dict[str, Any]]:
    """Extract native feature importances from the fitted RandomForest regressor."""
    model_step = pipeline.named_steps["model"]
    if isinstance(model_step, TransformedTargetRegressor):
        rf_regressor = model_step.regressor_
    else:
        rf_regressor = model_step

    if not hasattr(rf_regressor, "feature_importances_"):
        return []

    importances = rf_regressor.feature_importances_
    results = []
    for name, imp in zip(feature_names, importances):
        results.append({
            "feature": name,
            "importance": round(float(imp), 4),
            "percentage": round(float(imp) * 100, 2),
        })

    # Sort descending
    results.sort(key=lambda x: x["importance"], reverse=True)
    return results

