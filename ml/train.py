import os
import joblib
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from preprocess import preprocess_data

# ==========================
# Training Configuration
# ==========================

# HACKATHON:
# Change this path if your new dataset has a different file name.
DATASET_PATH = "datasets/flood.csv"

# Folder to save the trained model
MODEL_FOLDER = "models"
MODEL_NAME = "model.pkl"


def train_model():

    print("Loading dataset...")

    X, y = preprocess_data(DATASET_PATH)

    print("Dataset loaded successfully.")
    print(f"Features : {X.shape[1]}")
    print(f"Records  : {X.shape[0]}")

    print("\nSplitting dataset...")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42
    )

    print("Training Random Forest Model...")

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    print("Model training completed.")

    print("\nEvaluating model...")

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    print("\n========== Model Performance ==========")
    print(f"MAE       : {mae:.4f}")
    print(f"MSE       : {mse:.4f}")
    print(f"RMSE      : {rmse:.4f}")
    print(f"R² Score  : {r2:.4f}")

    os.makedirs(MODEL_FOLDER, exist_ok=True)

    model_path = os.path.join(MODEL_FOLDER, MODEL_NAME)

    joblib.dump(model, model_path)

    print(f"\nModel saved successfully at:")
    print(model_path)

    return model


if __name__ == "__main__":
    train_model()