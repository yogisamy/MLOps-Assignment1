"""FastAPI application for heart disease prediction."""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from api.schemas import PatientFeatures, PredictionResponse
from src.predict import load_model, predict as run_predict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
)
logger = logging.getLogger("heart_disease_api")

REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "API request latency in seconds",
    ["endpoint"],
)
PREDICTION_COUNT = Counter(
    "predictions_total",
    "Total predictions made",
    ["label"],
)

_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model
    logger.info("Loading model...")
    _model = load_model()
    logger.info("Model loaded successfully.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Heart Disease Prediction API",
    description="MLOps Assignment 01 – BITS Pilani AIMLCZG523",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    logger.info(
        "%s %s  status=%d  duration=%.3fs",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


@app.get("/", summary="Health check")
async def root():
    return {"status": "ok", "service": "Heart Disease Prediction API"}


@app.get("/health", summary="Health check")
async def health():
    return {"status": "healthy", "model_loaded": _model is not None}


@app.post("/predict", response_model=PredictionResponse, summary="Predict heart disease risk")
async def predict(features: PatientFeatures):
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        result = run_predict(features.model_dump(), model=_model)
        PREDICTION_COUNT.labels(label=result["label"]).inc()
        logger.info("Prediction: %s  confidence=%.4f", result["label"], result["confidence"])
        return result
    except Exception as exc:
        logger.exception("Prediction failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/metrics", summary="Prometheus metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
