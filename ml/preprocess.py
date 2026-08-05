import pandas as pd

# Target column used for training
TARGET_COLUMN = "FloodProbability"  # Change this if the hackathon dataset has a different target


# Load the dataset from CSV
def load_dataset(csv_path):
    df = pd.read_csv(csv_path)
    return df


# Check if the dataset is ready for training
def validate_dataset(df):

    # Check if the target column exists
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"'{TARGET_COLUMN}' column not found in the dataset.")

    # Check for missing values
    if df.isnull().sum().sum() != 0:
        raise ValueError("Dataset contains missing values.")

    # Check for duplicate rows
    if df.duplicated().sum() > 0:
        print("Warning: Duplicate rows found in the dataset.")


# Separate input features and target column
def prepare_features(df):

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    return X, y


# Complete preprocessing pipeline
def preprocess_data(csv_path):

    # Load dataset
    df = load_dataset(csv_path)

    # Validate dataset
    validate_dataset(df)

    # Split into features and target
    X, y = prepare_features(df)

    return X, y