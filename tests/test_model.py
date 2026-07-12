"""Unit tests for model training and prediction."""

import numpy as np
import pandas as pd
import pytest

from src.data_processing import build_preprocessor, prepare_data
from src.train import (
    compute_metrics,
    train_logistic_regression,
    train_random_forest,
)


@pytest.fixture
def synthetic_data():
    np.random.seed(42)
    n = 200
    df = pd.DataFrame(
        {
            "age": np.random.randint(29, 77, n).astype(float),
            "sex": np.random.randint(0, 2, n).astype(float),
            "cp": np.random.randint(0, 4, n).astype(float),
            "trestbps": np.random.randint(94, 200, n).astype(float),
            "chol": np.random.randint(126, 564, n).astype(float),
            "fbs": np.random.randint(0, 2, n).astype(float),
            "restecg": np.random.randint(0, 3, n).astype(float),
            "thalach": np.random.randint(71, 202, n).astype(float),
            "exang": np.random.randint(0, 2, n).astype(float),
            "oldpeak": np.random.uniform(0, 6.2, n),
            "slope": np.random.randint(0, 3, n).astype(float),
            "ca": np.random.randint(0, 4, n).astype(float),
            "thal": np.random.choice([1.0, 2.0, 3.0], n),
            "target": np.random.randint(0, 2, n),
        }
    )
    return prepare_data(df)


def test_compute_metrics_keys(synthetic_data):
    X_train, X_test, y_train, y_test = synthetic_data
    preprocessor = build_preprocessor()
    model, _ = train_logistic_regression(X_train, y_train, preprocessor)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    metrics = compute_metrics(y_test, y_pred, y_prob)
    for key in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
        assert key in metrics
        assert 0.0 <= metrics[key] <= 1.0


def test_logistic_regression_trains(synthetic_data):
    X_train, X_test, y_train, y_test = synthetic_data
    model, params = train_logistic_regression(X_train, y_train, build_preprocessor())
    assert hasattr(model, "predict")
    assert "clf__C" in params or any("C" in k for k in params)


def test_random_forest_trains(synthetic_data):
    X_train, X_test, y_train, y_test = synthetic_data
    model, params = train_random_forest(X_train, y_train, build_preprocessor())
    assert hasattr(model, "predict")
    preds = model.predict(X_test)
    assert set(preds).issubset({0, 1})


def test_model_predict_proba_range(synthetic_data):
    X_train, X_test, y_train, y_test = synthetic_data
    model, _ = train_random_forest(X_train, y_train, build_preprocessor())
    probs = model.predict_proba(X_test)
    assert probs.shape[1] == 2
    assert np.all(probs >= 0) and np.all(probs <= 1)
    assert np.allclose(probs.sum(axis=1), 1.0)
