"""Integration tests for FastAPI endpoints."""
import numpy as np
import pandas as pd
import pytest
import joblib
import os
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

SAMPLE_PAYLOAD = {
    "age": 63, "sex": 1, "cp": 3, "trestbps": 145,
    "chol": 233, "fbs": 1, "restecg": 0, "thalach": 150,
    "exang": 0, "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1.0,
}


def _make_mock_model():
    mock = MagicMock()
    mock.predict.return_value = np.array([1])
    mock.predict_proba.return_value = np.array([[0.2, 0.8]])
    return mock


@pytest.fixture
def client():
    mock_model = _make_mock_model()
    with patch("api.main._model", mock_model):
        from api.main import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Heart Disease" in resp.json()["service"]


def test_predict_endpoint_valid(client):
    resp = client.post("/predict", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert "prediction" in body
    assert "confidence" in body
    assert "label" in body
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["prediction"] in (0, 1)


def test_predict_missing_field(client):
    payload = {k: v for k, v in SAMPLE_PAYLOAD.items() if k != "age"}
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 422


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"api_requests_total" in resp.content or b"# HELP" in resp.content
