# Heart Disease Prediction – MLOps Assignment 01

**Course:** Machine Learning Operations (AIMLCZG523) – BITS Pilani  
**Dataset:** Heart Disease UCI Dataset (UCI ML Repository)  
**Stack:** Python · Scikit-learn · MLflow · FastAPI · Docker · Kubernetes · GitHub Actions · Prometheus · Grafana

---

## Project Structure

```
Assignment1/
├── data/
│   ├── download_data.py        # Dataset download script
│   └── heart.csv               # Downloaded dataset (git-ignored)
├── notebooks/
│   ├── 01_eda.py               # EDA script (generates figures/)
│   └── figures/                # EDA plots (auto-generated)
├── src/
│   ├── data_processing.py      # Preprocessing pipeline
│   ├── train.py                # Model training + MLflow logging
│   └── predict.py              # Inference helpers
├── api/
│   ├── main.py                 # FastAPI application
│   └── schemas.py              # Pydantic request/response schemas
├── tests/
│   ├── test_data_processing.py
│   ├── test_model.py
│   └── test_api.py
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── monitoring/
│   └── prometheus.yml
├── .github/workflows/ci.yml    # GitHub Actions CI/CD
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── setup.cfg
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd Assignment1
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Download Dataset

```bash
python data/download_data.py
```

### 3. Run EDA

```bash
PYTHONPATH=. python notebooks/01_eda.py
# Figures saved to notebooks/figures/
```

### 4. Train Models

```bash
PYTHONPATH=. python -m src.train
```

MLflow UI:
```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
# Open http://localhost:5000
```

### 5. Run Tests

```bash
PYTHONPATH=. pytest tests/ -v --cov=src --cov=api
```

### 6. Run API Locally

```bash
PYTHONPATH=. uvicorn api.main:app --reload
# Swagger UI: http://localhost:8000/docs
```

Test prediction:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 63, "sex": 1, "cp": 3, "trestbps": 145,
    "chol": 233, "fbs": 1, "restecg": 0, "thalach": 150,
    "exang": 0, "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1
  }'
```

---

## Docker

### Build & Run

```bash
docker build -t heart-disease-api:latest .
docker run -p 8000:8000 heart-disease-api:latest
```

### Full Stack (API + Prometheus + Grafana)

```bash
docker-compose up --build
```

| Service    | URL                    |
|------------|------------------------|
| API        | http://localhost:8000  |
| Swagger UI | http://localhost:8000/docs |
| Prometheus | http://localhost:9090  |
| Grafana    | http://localhost:3000  |

---

## Kubernetes (Minikube / Docker Desktop)

```bash
# Enable Kubernetes in Docker Desktop or start minikube
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods
kubectl get services

# Get URL (Minikube)
minikube service heart-disease-api-service --url
```

---

## API Endpoints

| Method | Endpoint   | Description               |
|--------|------------|---------------------------|
| GET    | /          | Health check              |
| GET    | /health    | Liveness check            |
| POST   | /predict   | Heart disease prediction  |
| GET    | /metrics   | Prometheus metrics        |
| GET    | /docs      | Swagger UI                |

### /predict Request Body

```json
{
  "age": 63,
  "sex": 1,
  "cp": 3,
  "trestbps": 145,
  "chol": 233,
  "fbs": 1,
  "restecg": 0,
  "thalach": 150,
  "exang": 0,
  "oldpeak": 2.3,
  "slope": 0,
  "ca": 0,
  "thal": 1
}
```

### /predict Response

```json
{
  "prediction": 1,
  "label": "Heart Disease Detected",
  "confidence": 0.82
}
```

---

## Models

| Model               | Tuning           | Metrics tracked             |
|---------------------|------------------|-----------------------------|
| Logistic Regression | GridSearchCV     | Accuracy, Precision, Recall |
| Random Forest       | GridSearchCV     | F1, ROC-AUC                 |

Best model is saved to `models/best_model.joblib` and selected by ROC-AUC.

---

## CI/CD (GitHub Actions)

Pipeline triggers on push/PR to `main`:

1. **Lint** – flake8 + black check  
2. **Unit tests** – pytest with coverage report  
3. **Train** – downloads data, trains models, logs to MLflow  
4. **Docker build** – builds image and runs smoke test  

See `.github/workflows/ci.yml`.

---

## Monitoring

- **Prometheus** scrapes `/metrics` every 15 s  
- **Grafana** dashboards at `http://localhost:3000` (admin/admin)  
- Metrics exposed: `api_requests_total`, `api_request_latency_seconds`, `predictions_total`

---

## Dataset Features

| Feature   | Description                            |
|-----------|----------------------------------------|
| age       | Age in years                           |
| sex       | 1 = male, 0 = female                   |
| cp        | Chest pain type (0–3)                  |
| trestbps  | Resting blood pressure (mmHg)          |
| chol      | Serum cholesterol (mg/dl)              |
| fbs       | Fasting blood sugar > 120 mg/dl        |
| restecg   | Resting ECG results (0–2)              |
| thalach   | Maximum heart rate achieved            |
| exang     | Exercise induced angina                |
| oldpeak   | ST depression induced by exercise      |
| slope     | Slope of peak exercise ST segment      |
| ca        | Number of major vessels (0–3)          |
| thal      | Thalassemia type                       |
| **target**| **0 = No disease, 1 = Disease**        |
