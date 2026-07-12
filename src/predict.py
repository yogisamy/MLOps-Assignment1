"""Inference helpers shared by API and CLI."""

import os
import joblib
import pandas as pd

from src.data_processing import NUMERICAL_FEATURES, CATEGORICAL_FEATURES

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
BEST_MODEL_PATH = os.path.join(MODELS_DIR, "best_model.joblib")


def load_model(path: str = BEST_MODEL_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found at {path}. Run `python -m src.train` first.")
    return joblib.load(path)


def predict(features: dict, model=None):
    if model is None:
        model = load_model()

    all_features = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    df = pd.DataFrame([features])[all_features]

    prediction = int(model.predict(df)[0])
    probability = float(model.predict_proba(df)[0][1])
    label = "Heart Disease Detected" if prediction == 1 else "No Heart Disease"

    return {
        "prediction": prediction,
        "label": label,
        "confidence": round(probability, 4),
    }
