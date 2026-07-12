"""
EDA script for Heart Disease UCI Dataset.
Run: python notebooks/01_eda.py
Generates plots in notebooks/figures/
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from src.data_processing import load_data, get_missing_summary

FIGURES_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)


def save(fig, name):
    path = os.path.join(FIGURES_DIR, name)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  Saved {path}")


def run_eda():
    df = load_data()
    print(f"Dataset shape: {df.shape}")
    print(df.dtypes)
    print("\nFirst 5 rows:")
    print(df.head())

    # --- 1. Missing value analysis ---
    print("\n--- Missing Values ---")
    summary = get_missing_summary(df)
    print(summary[summary["missing_count"] > 0])

    fig, ax = plt.subplots(figsize=(8, 4))
    summary["missing_pct"].sort_values(ascending=False).plot.bar(ax=ax, color="steelblue")
    ax.set_title("Missing Value Percentage per Feature")
    ax.set_ylabel("% Missing")
    ax.set_xlabel("Feature")
    save(fig, "01_missing_values.png")

    # --- 2. Class distribution ---
    fig, ax = plt.subplots(figsize=(5, 4))
    counts = df["target"].value_counts()
    ax.bar(["No Disease (0)", "Disease (1)"], counts.values, color=["#4CAF50", "#F44336"])
    for i, v in enumerate(counts.values):
        ax.text(i, v + 1, str(v), ha="center", fontweight="bold")
    ax.set_title("Class Distribution – Heart Disease Target")
    ax.set_ylabel("Count")
    save(fig, "02_class_distribution.png")

    # --- 3. Histograms of numerical features ---
    num_cols = ["age", "trestbps", "chol", "thalach", "oldpeak", "ca"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, col in zip(axes.flatten(), num_cols):
        df[col].dropna().hist(ax=ax, bins=25, color="steelblue", edgecolor="white")
        ax.set_title(col)
        ax.set_xlabel(col)
        ax.set_ylabel("Frequency")
    fig.suptitle("Histograms of Numerical Features", fontsize=14)
    plt.tight_layout()
    save(fig, "03_histograms.png")

    # --- 4. Correlation heatmap ---
    fig, ax = plt.subplots(figsize=(10, 8))
    corr = df.select_dtypes(include=np.number).corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f", cmap="coolwarm",
        center=0, linewidths=0.5, ax=ax,
    )
    ax.set_title("Correlation Heatmap")
    save(fig, "04_correlation_heatmap.png")

    # --- 5. Feature distributions by target ---
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    for ax, col in zip(axes.flatten(), num_cols):
        for label, grp in df.groupby("target"):
            grp[col].dropna().plot.kde(ax=ax, label=f"Target={label}")
        ax.set_title(f"{col} by Target")
        ax.legend()
    fig.suptitle("Feature Distribution by Heart Disease Presence", fontsize=14)
    plt.tight_layout()
    save(fig, "05_feature_by_target.png")

    # --- 6. Categorical feature counts by target ---
    cat_cols = ["sex", "cp", "fbs", "exang", "slope", "thal"]
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    for ax, col in zip(axes.flatten(), cat_cols):
        ct = df.groupby([col, "target"]).size().unstack(fill_value=0)
        ct.plot.bar(ax=ax, stacked=False)
        ax.set_title(f"{col} by Target")
        ax.set_xlabel(col)
        ax.legend(title="Target")
        ax.tick_params(axis="x", rotation=0)
    fig.suptitle("Categorical Feature Counts by Target", fontsize=14)
    plt.tight_layout()
    save(fig, "06_categorical_by_target.png")

    print("\nEDA complete. Figures saved to:", FIGURES_DIR)


if __name__ == "__main__":
    run_eda()
