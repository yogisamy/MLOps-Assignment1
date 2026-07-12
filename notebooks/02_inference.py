"""
Standalone inference script.
Loads the best trained model and runs predictions on sample and test data.
Run: PYTHONPATH=. python notebooks/02_inference.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from sklearn.metrics import classification_report

from src.data_processing import load_data, prepare_data
from src.predict import load_model, predict


def run_inference():
    print("=" * 55)
    print("  Heart Disease Prediction – Inference Demo")
    print("=" * 55)

    model = load_model()
    print(f"\nLoaded model: {type(model.named_steps['clf']).__name__}")

    # --- 1. Single sample prediction ---
    sample = {
        "age": 63, "sex": 1, "cp": 3, "trestbps": 145,
        "chol": 233, "fbs": 1, "restecg": 0, "thalach": 150,
        "exang": 0, "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1,
    }
    result = predict(sample, model=model)
    print("\n--- Single Sample Prediction ---")
    print(f"  Input : {sample}")
    print(f"  Result: {result}")

    # --- 2. Batch inference on held-out test set ---
    df = load_data()
    X_train, X_test, y_train, y_test = prepare_data(df)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n--- Batch Inference on Test Set ---")
    print(f"  Test samples : {len(X_test)}")
    print(f"  Positive rate: {y_pred.mean():.2%}")

    print("\n--- Classification Report ---")
    print(classification_report(y_test, y_pred, target_names=["No Disease", "Heart Disease"]))

    # Show a few predictions with confidence
    preview = X_test.copy().reset_index(drop=True)
    preview["actual"] = y_test.values
    preview["predicted"] = y_pred
    preview["confidence"] = y_prob.round(3)
    print("\n--- Sample Predictions (first 10) ---")
    print(preview[["age", "sex", "cp", "actual", "predicted", "confidence"]].head(10).to_string())


if __name__ == "__main__":
    run_inference()
