# Heart Disease Prediction – MLOps Assignment 01

**Course:** Machine Learning Operations (AIMLCZG523) – BITS Pilani  
**Dataset:** Heart Disease UCI Dataset (UCI ML Repository)  
**Stack:** Python · Scikit-learn · MLflow · FastAPI · Docker · Kubernetes · GitHub Actions · Prometheus · Grafana

---

## Project Structure

```
MLOps-Assignment1/
├── data/
│   ├── download_data.py        # Dataset download script
│   └── heart.csv               # Cleaned dataset (committed for reproducibility)
├── notebooks/
│   ├── 01_eda.py               # EDA script (generates figures/)
│   ├── 02_inference.py         # Inference demo script
│   └── figures/                # EDA plots (auto-generated, git-ignored)
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
├── screenshots/                # Evidence screenshots for the report
├── .github/workflows/ci.yml    # GitHub Actions CI/CD
├── generate_report.py          # Builds Assignment01_Report.docx
├── Assignment01_Report.docx    # Final written report
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── setup.cfg
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yogisamy/MLOps-Assignment1.git
cd MLOps-Assignment1
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Download Dataset

```bash
python3 data/download_data.py
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

| Model               | Hyperparameter Tuning                                          |
|---------------------|----------------------------------------------------------------|
| Logistic Regression | GridSearchCV — C, solver (5-fold StratifiedKFold)              |
| Random Forest       | GridSearchCV — n_estimators, max_depth, min_samples_split      |

Both models are evaluated on Accuracy, Precision, Recall, F1 and ROC-AUC
(test set + 5-fold cross-validation), and all runs are logged to MLflow.
The best model is selected by test ROC-AUC and saved to `models/best_model.joblib`.

---

## CI/CD (GitHub Actions)

Pipeline triggers on push to `main`/`develop` and PRs to `main`:

1. **Lint** – flake8 + black check  
2. **Download data** – `data/download_data.py`  
3. **Unit tests** – pytest with coverage report (uploaded as artifact)  
4. **Train** – trains both models, logs to MLflow, uploads model artifacts  
5. **Docker build & smoke test** – builds the image, runs the container and curls `/health`  

The pipeline fails fast: any lint, test, training or smoke-test error stops the run.
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
