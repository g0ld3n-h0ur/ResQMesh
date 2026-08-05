import os
import joblib
import pandas as pd

# Location of the trained model
MODEL_PATH = os.path.join("models", "model.pkl")

# Load the trained model only once
model = joblib.load(MODEL_PATH)


# Predict flood probability for new input
def predict(input_data):

    # If input is a dictionary, convert it to a DataFrame
    if isinstance(input_data, dict):
        input_data = pd.DataFrame([input_data])

    prediction = model.predict(input_data)

    return float(prediction[0])


# Run this file directly for quick testing
if __name__ == "__main__":

    sample_data = {
        "MonsoonIntensity": 5,
        "TopographyDrainage": 7,
        "RiverManagement": 5,
        "Deforestation": 6,
        "Urbanization": 5,
        "ClimateChange": 6,
        "DamsQuality": 7,
        "Siltation": 4,
        "AgriculturalPractices": 5,
        "Encroachments": 3,
        "IneffectiveDisasterPreparedness": 6,
        "DrainageSystems": 7,
        "CoastalVulnerability": 5,
        "Landslides": 2,
        "Watersheds": 6,
        "DeterioratingInfrastructure": 5,
        "PopulationScore": 7,
        "WetlandLoss": 5,
        "InadequatePlanning": 6,
        "PoliticalFactors": 4
    }

    result = predict(sample_data)

    print(f"Predicted Flood Probability: {result:.4f}")