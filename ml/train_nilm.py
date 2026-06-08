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
from sklearn.utils.class_weight import compute_sample_weight

try:
    from .feature_extraction import FEATURE_COLUMNS, load_and_extract
except ImportError:
    from feature_extraction import FEATURE_COLUMNS, load_and_extract

MODELS_DIR = Path(__file__).parent / "models"
DATA_DIR = Path(__file__).parent / "data"
RANDOM_SEED = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

# Feature-rich XGBoost baseline for low-frequency Tapo P110 appliance signatures.
XGB_PARAMS = {
    "n_estimators": 350,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.85,
    "colsample_bytree": 0.9,
    "min_child_weight": 1,
    "reg_lambda": 1.5,
    "eval_metric": "mlogloss",
    "random_state": RANDOM_SEED,
    "n_jobs": -1,
}

FEATURE_COLS = FEATURE_COLUMNS


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


def train(X_train, y_train):
    """Fit XGBoost classifier on training data."""
    try:
        import xgboost as xgb
    except ImportError as exc:
        raise RuntimeError(
            "xgboost is not installed. Install ML dependencies with: "
            "python -m pip install -r ml/requirements.txt"
        ) from exc

    model = xgb.XGBClassifier(**XGB_PARAMS)
    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)
    model.fit(X_train, y_train, sample_weight=sample_weight)
    return model


def cross_validate_model(model, X, y) -> dict:
    """Stratified k-fold cross-validation."""
    class_counts = np.bincount(y)
    min_class_count = int(class_counts.min()) if len(class_counts) else 0
    if min_class_count < 2:
        return {
            "cv_mean_accuracy": None,
            "cv_std_accuracy": None,
            "cv_fold_scores": [],
            "cv_folds": 0,
            "cv_skipped_reason": "Need at least 2 samples per class for stratified CV.",
        }

    n_splits = min(CV_FOLDS, min_class_count)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
    return {
        "cv_mean_accuracy": float(scores.mean()),
        "cv_std_accuracy": float(scores.std()),
        "cv_fold_scores": scores.tolist(),
        "cv_folds": n_splits,
    }


def split_train_test(X, y):
    """Use a stratified split only when every class has enough samples."""
    class_counts = np.bincount(y)
    n_classes = len(class_counts)
    test_count = int(np.ceil(len(y) * TEST_SIZE))
    train_count = len(y) - test_count
    can_split = (
        len(y) >= 2
        and n_classes > 1
        and int(class_counts.min()) >= 2
        and test_count >= n_classes
        and train_count >= n_classes
    )

    if can_split:
        return (*train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
        ), True)

    print("Skipping stratified test split: need more samples per appliance class.")
    return X, None, y, None, False


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


def get_feature_importance(model, feature_cols: list[str], limit: int = 12) -> list[dict]:
    """Return top model feature importances when available."""
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return []
    pairs = sorted(
        zip(feature_cols, importances),
        key=lambda item: float(item[1]),
        reverse=True,
    )
    return [
        {"feature": name, "importance": float(score)}
        for name, score in pairs[:limit]
    ]


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
    X_train, X_test, y_train, y_test, has_test_split = split_train_test(X, y)
    test_count = len(X_test) if has_test_split else 0
    print(f"Train: {len(X_train)} samples | Test: {test_count} samples")

    model = train(X_train, y_train)

    train_acc = float((model.predict(X_train) == y_train).mean())
    test_acc = (
        float((model.predict(X_test) == y_test).mean())
        if has_test_split
        else None
    )
    print(f"Train accuracy : {train_acc:.4f}")
    if test_acc is None:
        print("Test  accuracy : skipped")
    else:
        print(f"Test  accuracy : {test_acc:.4f}")

    cv_results = cross_validate_model(model, X, y)
    if cv_results["cv_mean_accuracy"] is None:
        print(f"CV mean        : skipped ({cv_results['cv_skipped_reason']})")
    else:
        print(f"CV mean        : {cv_results['cv_mean_accuracy']:.4f} +/- {cv_results['cv_std_accuracy']:.4f}")

    metadata = {
        "train_samples": int(len(X_train)),
        "test_samples": int(test_count),
        "total_feature_windows": int(len(df)),
        "n_classes": int(le.classes_.shape[0]),
        "classes": le.classes_.tolist(),
        "class_distribution": {
            label: int(count)
            for label, count in df["appliance_label"].value_counts().items()
        },
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "has_test_split": has_test_split,
        "feature_set_version": "tapo_signature_v2",
        "feature_cols": FEATURE_COLS,
        "top_feature_importance": get_feature_importance(model, FEATURE_COLS),
        "xgb_params": XGB_PARAMS,
        "window_size_s": args.window,
        "notes": (
            "This is a smart-plug appliance signature classifier. It is not yet "
            "aggregate household NILM disaggregation."
        ),
        **cv_results,
    }
    save_model(model, le, metadata)
    print("\nTraining complete.")


if __name__ == "__main__":
    main()
