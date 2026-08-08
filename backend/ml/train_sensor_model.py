import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "flood_model.pkl")

FLOOD_FEATURE_COLUMNS = [
    "rainfall_mm",
    "river_level_m",
    "soil_moisture_pct",
    "temperature_c",
    "humidity_pct",
    "previous_flood_events",
    "elevation_m",
    "population_density",
]

def generate_synthetic_data(num_samples=5000, seed=42):
    """
    Generate a physically consistent synthetic dataset for flood prediction.
    
    Logical rules applied:
      - Higher rainfall, higher river levels, and higher soil moisture increase probability.
      - Lower terrain elevation increases probability (water pools in low areas).
      - Previous flood history and high humidity have minor positive impact.
      - Temperature and population density are neutral.
    """
    np.random.seed(seed)
    
    # Generate random features within realistic ranges
    rainfall = np.random.uniform(0.0, 300.0, num_samples)          # 0 to 300 mm
    river_level = np.random.uniform(0.5, 10.0, num_samples)         # 0.5 to 10 m
    soil_moisture = np.random.uniform(10.0, 100.0, num_samples)     # 10% to 100%
    temperature = np.random.uniform(15.0, 45.0, num_samples)        # 15 to 45 C
    humidity = np.random.uniform(40.0, 100.0, num_samples)          # 40% to 100%
    prev_events = np.random.randint(0, 8, num_samples).astype(float)# 0 to 7 events
    elevation = np.random.uniform(0.0, 500.0, num_samples)          # 0 to 500 m
    pop_density = np.random.uniform(50.0, 10000.0, num_samples)     # 50 to 10000 ppl/km2
    
    # Compute base risk score [0, 1]
    # Weights sum to 1.0 (excluding elevation subtraction which is scaled appropriately)
    score = (
        (rainfall / 300.0) * 0.40 +
        (river_level / 10.0) * 0.35 +
        (soil_moisture / 100.0) * 0.10 +
        (1.0 - (elevation / 500.0)) * 0.08 +
        (prev_events / 7.0) * 0.04 +
        (humidity / 100.0) * 0.03
    )
    
    # Add random Gaussian noise to make it realistic
    noise = np.random.normal(0, 0.03, num_samples)
    probability = np.clip(score + noise, 0.0, 1.0)
    
    df = pd.DataFrame({
        "rainfall_mm": rainfall,
        "river_level_m": river_level,
        "soil_moisture_pct": soil_moisture,
        "temperature_c": temperature,
        "humidity_pct": humidity,
        "previous_flood_events": prev_events,
        "elevation_m": elevation,
        "population_density": pop_density,
        "FloodProbability": probability
    })
    
    return df

def train_model():
    print("Generating synthetic sensor logs...")
    df = generate_synthetic_data(num_samples=10000)
    
    X = df[FLOOD_FEATURE_COLUMNS]
    y = df["FloodProbability"]
    
    print(f"Features: {FLOOD_FEATURE_COLUMNS}")
    print(f"Training size: {X.shape[0]} records")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train RandomForestRegressor
    print("Training Random Forest Regressor model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    print("Training complete.")
    
    # Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    print("\n========== Model Performance ==========")
    print(f"Mean Absolute Error (MAE) : {mae:.4f}")
    print(f"R² Score                  : {r2:.4f}")
    print("=======================================")
    
    # Save
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nTrained model successfully saved to:\n{MODEL_PATH}")

if __name__ == "__main__":
    train_model()
