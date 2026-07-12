"""Download Heart Disease UCI Dataset and save to data/heart.csv."""
import os
import ssl
import pandas as pd

# macOS ships without CA certs for the Python framework; bypass verification
ssl._create_default_https_context = ssl._create_unverified_context

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(DATA_DIR, "heart.csv")


def download_dataset():
    try:
        from ucimlrepo import fetch_ucirepo

        print("Fetching Heart Disease dataset from UCI ML Repository...")
        heart_disease = fetch_ucirepo(id=45)
        X = heart_disease.data.features
        y = heart_disease.data.targets

        df = pd.concat([X, y], axis=1)
        # Standardise target: binarise (0 = no disease, 1 = disease)
        df.columns = [
            "age", "sex", "cp", "trestbps", "chol", "fbs",
            "restecg", "thalach", "exang", "oldpeak", "slope",
            "ca", "thal", "target",
        ]
        df["target"] = (df["target"] > 0).astype(int)
        df.to_csv(OUTPUT_PATH, index=False)
        print(f"Dataset saved to {OUTPUT_PATH}  ({len(df)} rows)")
        return df

    except Exception as e:
        print(f"ucimlrepo failed ({e}), falling back to manual URL download...")
        url = (
            "https://archive.ics.uci.edu/ml/machine-learning-databases"
            "/heart-disease/processed.cleveland.data"
        )
        cols = [
            "age", "sex", "cp", "trestbps", "chol", "fbs",
            "restecg", "thalach", "exang", "oldpeak", "slope",
            "ca", "thal", "target",
        ]
        df = pd.read_csv(url, names=cols, na_values="?")
        df["target"] = (df["target"] > 0).astype(int)
        df.to_csv(OUTPUT_PATH, index=False)
        print(f"Dataset saved to {OUTPUT_PATH}  ({len(df)} rows)")
        return df


if __name__ == "__main__":
    download_dataset()
