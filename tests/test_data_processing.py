"""Unit tests for data_processing module."""

import numpy as np
import pandas as pd
import pytest

from src.data_processing import (
    build_preprocessor,
    get_feature_names,
    get_missing_summary,
    prepare_data,
    TARGET,
)


@pytest.fixture
def sample_df():
    np.random.seed(0)
    n = 100
    return pd.DataFrame(
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


def test_feature_names():
    num, cat = get_feature_names()
    assert len(num) > 0
    assert len(cat) > 0
    assert "age" in num
    assert "sex" in cat


def test_prepare_data_shapes(sample_df):
    X_train, X_test, y_train, y_test = prepare_data(sample_df, test_size=0.2)
    assert len(X_train) + len(X_test) == len(sample_df)
    assert len(y_train) == len(X_train)
    assert len(y_test) == len(X_test)


def test_prepare_data_no_target_leakage(sample_df):
    X_train, X_test, y_train, y_test = prepare_data(sample_df)
    assert TARGET not in X_train.columns
    assert TARGET not in X_test.columns


def test_preprocessor_returns_pipeline():
    p = build_preprocessor()
    assert isinstance(p, object)


def test_preprocessor_transforms(sample_df):
    X_train, X_test, y_train, y_test = prepare_data(sample_df)
    preprocessor = build_preprocessor()
    X_transformed = preprocessor.fit_transform(X_train)
    assert X_transformed.shape[0] == len(X_train)
    assert not np.isnan(X_transformed).any()


def test_missing_summary(sample_df):
    sample_df.loc[0, "age"] = np.nan
    summary = get_missing_summary(sample_df)
    assert "missing_count" in summary.columns
    assert summary.loc["age", "missing_count"] == 1


def test_prepare_data_handles_missing(sample_df):
    sample_df.loc[:5, "chol"] = np.nan
    X_train, X_test, y_train, y_test = prepare_data(sample_df)
    preprocessor = build_preprocessor()
    X_transformed = preprocessor.fit_transform(X_train)
    assert not np.isnan(X_transformed).any()
