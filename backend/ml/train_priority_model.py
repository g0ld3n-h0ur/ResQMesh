"""
ml/train_priority_model.py

Trains two real models on the hackathon-provided dataset
(ml/datasets/disaster_relief_resource_allocation.csv, 200k rows):

  1. RandomForestClassifier  -> allocation_priority   (Low/Medium/High/Critical)
  2. RandomForestRegressor   -> recommended_relief_units (continuous)

Both are full scikit-learn Pipelines (preprocessing + estimator saved together),
so predict.py never has to re-implement encoding/imputation by hand — it just
hands the pipeline a single-row DataFrame with the same column names used here.

Usage
-----
    python ml/train_priority_model.py

Requires ml/datasets/disaster_relief_resource_allocation.csv to be present
(gitignored — copy the hackathon-provided CSV there before running).
"""

import os

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATASET_PATH = os.path.join(os.path.dirname(__file__), "datasets", "disaster_relief_resource_allocation.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
CLASSIFIER_PATH = os.path.join(MODEL_DIR, "priority_classifier.pkl")
REGRESSOR_PATH = os.path.join(MODEL_DIR, "relief_units_regressor.pkl")

# Practical, report-time-knowable input features. Order matters — predict.py
# builds inference rows with this exact same column list.
NUMERIC_FEATURES = [
    "population_affected",
    "households_affected",
    "infrastructure_damage_score",
    "nearest_relief_center_distance_km",
    "available_volunteers",
    "medical_teams_available",
    "food_stock_kg",
    "water_stock_liters",
    "shelter_capacity",
    "funding_available_usd",
    "vulnerability_index",
    "ngo_present",
    "government_response_active",
]
CATEGORICAL_FEATURES = [
    "disaster_type",
    "severity_level",
    "accessibility_status",
    "communication_status",
    "power_status",
]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

PRIORITY_TARGET = "allocation_priority"
RELIEF_UNITS_TARGET = "recommended_relief_units"


def _build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline([("impute", SimpleImputer(strategy="median"))])
    categorical_pipeline = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def load_dataset() -> pd.DataFrame:
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found at {DATASET_PATH}. Copy the hackathon-provided "
            "disaster_relief_resource_allocation.csv into backend/ml/datasets/ first."
        )
    df = pd.read_csv(DATASET_PATH)
    # Booleans arrive as True/False from pandas; cast to int so the numeric
    # imputer/pipeline can treat them uniformly with the other numeric columns.
    for col in ("ngo_present", "government_response_active"):
        df[col] = df[col].astype(int)
    return df


def train_priority_classifier(df: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("Training allocation_priority classifier")
    print("=" * 70)

    X = df[FEATURE_COLUMNS]
    y = df[PRIORITY_TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline(
        [
            ("preprocess", _build_preprocessor()),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=120,
                    max_depth=10,
                    min_samples_leaf=40,
                    max_samples=0.5,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    macro_f1 = f1_score(y_test, predictions, average="macro")

    print(f"Test accuracy : {accuracy:.4f}")
    print(f"Macro F1      : {macro_f1:.4f}")
    print("\nPer-class report:")
    print(classification_report(y_test, predictions))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(pipeline, CLASSIFIER_PATH)
    print(f"Saved -> {CLASSIFIER_PATH}")


def train_relief_units_regressor(df: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("Training recommended_relief_units regressor")
    print("=" * 70)

    X = df[FEATURE_COLUMNS]
    y = df[RELIEF_UNITS_TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=df[PRIORITY_TARGET]
    )

    pipeline = Pipeline(
        [
            ("preprocess", _build_preprocessor()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=120,
                    max_depth=10,
                    min_samples_leaf=40,
                    max_samples=0.5,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"Test MAE      : {mae:.1f} relief units")
    print(f"Test R²       : {r2:.4f}")
    print(f"(target mean={y_test.mean():.1f}, std={y_test.std():.1f} — MAE should be well below std)")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(pipeline, REGRESSOR_PATH)
    print(f"Saved -> {REGRESSOR_PATH}")


def main() -> None:
    print(f"Loading dataset from {DATASET_PATH} ...")
    df = load_dataset()
    print(f"Loaded {len(df):,} rows, {len(FEATURE_COLUMNS)} input features.")

    train_priority_classifier(df)
    train_relief_units_regressor(df)

    print("\nDone. Both models are in backend/ml/models/.")


if __name__ == "__main__":
    main()
