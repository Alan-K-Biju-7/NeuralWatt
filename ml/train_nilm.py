"""
NILM appliance classifier training pipeline.

Algorithm: XGBoost classifier
Input:     labelled appliance CSV or pre-extracted features CSV
Output:    ml/models/nilm_v1.pkl + ml/models/nilm_v1_metadata.json

Usage:
    python train_nilm.py --data data/sample_appliance_data.csv
    python train_nilm.py --features data/features_extracted.csv
"""

import argparse
import pickle
import json
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

from feature_extraction import load_and_extract

MODELS_DIR = Path(__file__).parent / "models"
DATA_DIR = Path(__file__).parent / "data"
RANDOM_SEED = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

# Baseline hyperparameters — tune after real Tapo P110 data arrives
XGB_PARAMS = {
    "n_estimators": 200,
    "max_depth": 6,
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "eval_metric": "mlogloss",
    "random_state": RANDOM_SEED,
    "n_jobs": -1,
}

FEATURE_COLS = [
    "mean_power",
    "max_power",
    "min_power",
    "power_delta",
    "std_power",
    "rise_time_s",
    "steady_state_w",
    "is_cyclic",
    "on_fraction",
]


def load_features(path: str) -> pd.DataFrame:
    """Load a pre-extracted features CSV."""
    df = pd.read_csv(path)
    missing = set(FEATURE_COLS + ["appliance_label"]) - set(df.columns)
    if missing:
        raise ValueError(f"Feature CSV missing columns: {missing}")
    return df


def prepare_data(df: pd.DataFrame):
    """Encode labels and return X, y, label encoder."""
    le = LabelEncoder()
    X = df[FEATURE_COLS].values
    y = le.fit_transform(df["appliance_label"].values)
    return X, y, le


def train(X_train, y_train) -> xgb.XGBClassifier:
    """Fit XGBoost classifier on training data."""
    model = xgb.XGBClassifier(**XGB_PARAMS)
    model.fit(X_train, y_train)
    return model


def cross_validate_model(model, X, y) -> dict:
    """Stratified k-fold cross-validation."""
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
    return {
        "cv_mean_accuracy": float(scores.mean()),
        "cv_std_accuracy": float(scores.std()),
        "cv_fold_scores": scores.tolist(),
    }


def save_model(model, label_encoder: LabelEncoder, metadata: dict):
    """Serialize model artifact and save metadata JSON."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": model,
        "label_encoder": label_encoder,
        "feature_cols": FEATURE_COLS,
        "metadata": metadata,
    }
    model_path = MODELS_DIR / "nilm_v1.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(artifact, f)
    print(f"Model saved -> {model_path}")

    meta_path = MODELS_DIR / "nilm_v1_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved -> {meta_path}")


def main():
    parser = argparse.ArgumentParser(description="Train NeuralWatt NILM classifier")
    parser.add_argument("--data", type=str, help="Path to raw labelled appliance CSV")
    parser.add_argument("--features", type=str, help="Path to pre-extracted features CSV")
    parser.add_argument("--window", type=int, default=30, help="Window size in seconds")
    args = parser.parse_args()

    if args.features:
        print(f"Loading features from {args.features}")
        df = load_features(args.features)
    elif args.data:
        print(f"Extracting features from {args.data}")
        df = load_and_extract(args.data, window_size=args.window)
        out = DATA_DIR / "features_extracted.csv"
        df.to_csv(out, index=False)
        print(f"Features saved -> {out}")
    else:
        parser.error("Provide --data or --features")

    print(f"\nDataset: {len(df)} windows | {df['appliance_label'].nunique()} classes")
    print(f"Class distribution:\n{df['appliance_label'].value_counts()}\n")

    X, y, le = prepare_data(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )
    print(f"Train: {len(X_train)} samples | Test: {len(X_test)} samples")

    model = train(X_train, y_train)

    train_acc = float((model.predict(X_train) == y_train).mean())
    test_acc = float((model.predict(X_test) == y_test).mean())
    print(f"Train accuracy : {train_acc:.4f}")
    print(f"Test  accuracy : {test_acc:.4f}")

    cv_results = cross_validate_model(model, X, y)
    print(f"CV mean        : {cv_results['cv_mean_accuracy']:.4f} +/- {cv_results['cv_std_accuracy']:.4f}")

    metadata = {
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "n_classes": int(le.classes_.shape[0]),
        "classes": le.classes_.tolist(),
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "feature_cols": FEATURE_COLS,
        "xgb_params": XGB_PARAMS,
        "window_size_s": args.window,
        **cv_results,
    }
    save_model(model, le, metadata)
    print("\nTraining complete.")


if __name__ == "__main__":
    main()
