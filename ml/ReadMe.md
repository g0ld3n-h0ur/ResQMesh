# Disaster Relief AI - ML Module

This folder contains the Machine Learning component of the Disaster Relief Coordination Platform.

## Model Used

- Random Forest Regressor

## Folder Structure

```
ml/
│
├── datasets/
├── models/
├── notebooks/
├── outputs/
├── preprocess.py
├── train.py
├── predict.py
├── requirements.txt
└── README.md
```

## Files

- **datasets/** - Training dataset
- **models/** - Trained model (`model.pkl`)
- **notebooks/** - Google Colab notebook used for model development
- **preprocess.py** - Loads and prepares the dataset
- **train.py** - Trains the model and saves `model.pkl`
- **predict.py** - Loads the trained model and returns predictions

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Train the Model

```bash
python train.py
```

## Use the Model

```python
from predict import predict

result = predict(input_data)
print(result)
```

## Team

AI/ML Module