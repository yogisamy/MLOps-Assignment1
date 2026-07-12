"""Train, tune, evaluate and log two classification models with MLflow."""
import os
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import mlflow
import mlflow.sklearn
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (
    GridSearchCV,
    cross_val_score,
    StratifiedKFold,
)
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    RocCurveDisplay,
    ConfusionMatrixDisplay,
)

from src.data_processing import (
    load_data,
    prepare_data,
    build_preprocessor,
)

warnings.filterwarnings("ignore")

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

EXPERIMENT_NAME = "heart_disease_classification"


def compute_metrics(y_true, y_pred, y_prob) -> dict:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_prob),
    }


def save_confusion_matrix_plot(y_true, y_pred, model_name: str, tmp_dir: str) -> str:
    fig, ax = plt.subplots(figsize=(5, 4))
    ConfusionMatrixDisplay.from_predictions(y_true, y_pred, ax=ax)
    ax.set_title(f"Confusion Matrix – {model_name}")
    path = os.path.join(tmp_dir, f"confusion_matrix_{model_name}.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def save_roc_curve_plot(y_true, y_prob, model_name: str, tmp_dir: str) -> str:
    fig, ax = plt.subplots(figsize=(5, 4))
    RocCurveDisplay.from_predictions(y_true, y_prob, ax=ax, name=model_name)
    ax.set_title(f"ROC Curve – {model_name}")
    path = os.path.join(tmp_dir, f"roc_curve_{model_name}.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def train_logistic_regression(X_train, y_train, preprocessor):
    pipe = Pipeline([("preprocessor", preprocessor), ("clf", LogisticRegression(max_iter=1000))])

    param_grid = {
        "clf__C": [0.01, 0.1, 1, 10],
        "clf__solver": ["lbfgs", "liblinear"],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    gs = GridSearchCV(pipe, param_grid, cv=cv, scoring="roc_auc", n_jobs=-1)
    gs.fit(X_train, y_train)
    return gs.best_estimator_, gs.best_params_


def train_random_forest(X_train, y_train, preprocessor):
    pipe = Pipeline([("preprocessor", preprocessor), ("clf", RandomForestClassifier(random_state=42))])

    param_grid = {
        "clf__n_estimators": [100, 200],
        "clf__max_depth": [None, 5, 10],
        "clf__min_samples_split": [2, 5],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    gs = GridSearchCV(pipe, param_grid, cv=cv, scoring="roc_auc", n_jobs=-1)
    gs.fit(X_train, y_train)
    return gs.best_estimator_, gs.best_params_


def run_cross_validation(model, X_train, y_train, cv_folds: int = 5) -> dict:
    """Run k-fold CV and return mean ± std for key metrics."""
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    cv_metrics = {}
    for scoring in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)
        cv_metrics[f"cv_{scoring}_mean"] = round(float(scores.mean()), 4)
        cv_metrics[f"cv_{scoring}_std"] = round(float(scores.std()), 4)
    return cv_metrics


def log_model_to_mlflow(
    model,
    model_name: str,
    best_params: dict,
    metrics: dict,
    cv_metrics: dict,
    X_train,
    X_test,
    y_train,
    y_test,
    tmp_dir: str,
):
    with mlflow.start_run(run_name=model_name):
        mlflow.set_tag("model_name", model_name)

        for k, v in best_params.items():
            mlflow.log_param(k.replace("clf__", ""), v)

        for k, v in metrics.items():
            mlflow.log_metric(k, round(v, 4))

        for k, v in cv_metrics.items():
            mlflow.log_metric(k, v)

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        cm_path = save_confusion_matrix_plot(y_test, y_pred, model_name, tmp_dir)
        roc_path = save_roc_curve_plot(y_test, y_prob, model_name, tmp_dir)
        mlflow.log_artifact(cm_path, artifact_path="plots")
        mlflow.log_artifact(roc_path, artifact_path="plots")

        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_PICKLE,
        )

        model_path = os.path.join(MODELS_DIR, f"{model_name}.joblib")
        joblib.dump(model, model_path)
        mlflow.log_artifact(model_path, artifact_path="saved_model")

        run_id = mlflow.active_run().info.run_id
    return run_id


def run_training():
    import tempfile

    mlflow.set_experiment(EXPERIMENT_NAME)

    df = load_data()
    X_train, X_test, y_train, y_test = prepare_data(df)
    preprocessor = build_preprocessor()

    results = {}

    with tempfile.TemporaryDirectory() as tmp_dir:
        # --- Logistic Regression ---
        print("Training Logistic Regression...")
        lr_model, lr_params = train_logistic_regression(X_train, y_train, build_preprocessor())
        lr_pred = lr_model.predict(X_test)
        lr_prob = lr_model.predict_proba(X_test)[:, 1]
        lr_metrics = compute_metrics(y_test, lr_pred, lr_prob)
        print(f"  LR metrics: {lr_metrics}")
        lr_cv = run_cross_validation(lr_model, X_train, y_train)
        print(f"  LR CV (roc_auc): {lr_cv['cv_roc_auc_mean']:.4f} ± {lr_cv['cv_roc_auc_std']:.4f}")
        lr_run_id = log_model_to_mlflow(
            lr_model, "logistic_regression", lr_params, lr_metrics, lr_cv,
            X_train, X_test, y_train, y_test, tmp_dir
        )
        results["logistic_regression"] = {"metrics": lr_metrics, "cv_metrics": lr_cv, "run_id": lr_run_id}

        # --- Random Forest ---
        print("Training Random Forest...")
        rf_model, rf_params = train_random_forest(X_train, y_train, build_preprocessor())
        rf_pred = rf_model.predict(X_test)
        rf_prob = rf_model.predict_proba(X_test)[:, 1]
        rf_metrics = compute_metrics(y_test, rf_pred, rf_prob)
        print(f"  RF metrics: {rf_metrics}")
        rf_cv = run_cross_validation(rf_model, X_train, y_train)
        print(f"  RF CV (roc_auc): {rf_cv['cv_roc_auc_mean']:.4f} ± {rf_cv['cv_roc_auc_std']:.4f}")
        rf_run_id = log_model_to_mlflow(
            rf_model, "random_forest", rf_params, rf_metrics, rf_cv,
            X_train, X_test, y_train, y_test, tmp_dir
        )
        results["random_forest"] = {"metrics": rf_metrics, "cv_metrics": rf_cv, "run_id": rf_run_id}

    # Select best model
    best_name = max(results, key=lambda k: results[k]["metrics"]["roc_auc"])
    best_model = lr_model if best_name == "logistic_regression" else rf_model
    best_path = os.path.join(MODELS_DIR, "best_model.joblib")
    joblib.dump(best_model, best_path)
    print(f"\nBest model: {best_name}  (saved to {best_path})")
    print(f"  Metrics: {results[best_name]['metrics']}")

    return results


if __name__ == "__main__":
    run_training()
