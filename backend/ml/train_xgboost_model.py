import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier, XGBRegressor

DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "datasets",
    "disaster_relief_resource_allocation.csv"
)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

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
RELIEF_TARGET = "recommended_relief_units"


def main():
    print("Loading dataset...")
    df = pd.read_csv(DATASET_PATH)

    print(f"Loaded {len(df):,} rows")

    # Convert booleans
    for col in ["ngo_present", "government_response_active"]:
        df[col] = df[col].astype(int)

    # One-hot encode categorical features
    X = pd.get_dummies(
        df[FEATURE_COLUMNS],
        columns=CATEGORICAL_FEATURES,
        dummy_na=True
    )

    X = X.fillna(0)

    # ---------------------------------------------------------
    # CLASSIFICATION
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("Training XGBoost Classifier")
    print("=" * 60)

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df[PRIORITY_TARGET])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    classifier = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1
    )

    classifier.fit(X_train, y_train)

    predictions = classifier.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    macro_f1 = f1_score(y_test, predictions, average="macro")

    print(f"Test accuracy : {accuracy:.4f}")
    print(f"Macro F1      : {macro_f1:.4f}")

    print("\nPer-class report:")
    print(
        classification_report(
            y_test,
            predictions,
            target_names=label_encoder.classes_
        )
    )

    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(
        classifier,
        os.path.join(MODEL_DIR, "xgb_priority_classifier.pkl")
    )

    joblib.dump(
        label_encoder,
        os.path.join(MODEL_DIR, "xgb_priority_label_encoder.pkl")
    )

    joblib.dump(
        list(X.columns),
        os.path.join(MODEL_DIR, "xgb_feature_columns.pkl")
    )

    # ---------------------------------------------------------
    # REGRESSION
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("Training XGBoost Regressor")
    print("=" * 60)

    y_reg = df[RELIEF_TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_reg,
        test_size=0.2,
        random_state=42
    )

    regressor = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        eval_metric="mae",
        random_state=42,
        n_jobs=-1
    )

    regressor.fit(X_train, y_train)

    predictions = regressor.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"Test MAE      : {mae:.1f} relief units")
    print(f"Test R²       : {r2:.4f}")

    joblib.dump(
        regressor,
        os.path.join(MODEL_DIR, "xgb_relief_units_regressor.pkl")
    )

    print("\nXGBoost training complete.")
    print("Models saved to backend/ml/models/")


if __name__ == "__main__":
    main()