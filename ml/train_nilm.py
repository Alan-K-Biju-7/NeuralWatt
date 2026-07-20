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
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight

try:
    from .feature_extraction import FEATURE_COLUMNS, FEATURE_SET_VERSION, load_and_extract
except ImportError:
    from feature_extraction import FEATURE_COLUMNS, FEATURE_SET_VERSION, load_and_extract

MODELS_DIR = Path(__file__).parent / "models"
DATA_DIR = Path(__file__).parent / "data"
RANDOM_SEED = 42
CV_FOLDS = 5
GROUP_COLUMNS = ("capture_id", "session_id")
REMOVED_FEATURE_COLS = ["mean_voltage", "std_voltage", "mean_current", "max_current"]
NORMALIZED_SHAPE_FEATURES = [
    "peak_to_mean_ratio",
    "coefficient_of_variation",
    "duty_cycle",
    "delta_vs_rolling_baseline",
]

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
MIN_ACTIVE_WINDOW_POWER_W = 10.0


def filter_informative_windows(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Drop off-only windows before appliance classification training.

    A completely idle window is not a reliable appliance signature unless the
    dataset has an explicit "off/unknown" class, which this classifier does not.
    """
    if "max_power" not in df.columns:
        return df, 0
    mask = pd.to_numeric(df["max_power"], errors="coerce").fillna(0.0) > MIN_ACTIVE_WINDOW_POWER_W
    filtered = df.loc[mask].reset_index(drop=True)
    return filtered, int((~mask).sum())


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


def select_group_column(df: pd.DataFrame) -> tuple[str | None, np.ndarray | None]:
    """Choose capture/session metadata for group-aware validation."""
    for column in GROUP_COLUMNS:
        if column not in df.columns:
            continue
        groups = (
            df[column]
            .astype("string")
            .fillna("")
            .str.strip()
        )
        groups = groups.mask(groups == "", "__missing_group__")
        if int(groups.nunique()) >= 2:
            return column, groups.to_numpy(dtype=str)
    return None, None


def _skip_group_validation(reason: str) -> dict:
    return {
        "cv_mean_accuracy": None,
        "cv_std_accuracy": None,
        "cv_fold_scores": [],
        "cv_folds": 0,
        "cv_strategy": "group_kfold",
        "cv_skipped_reason": reason,
    }


def _valid_group_train_split(y_train: np.ndarray, all_classes: np.ndarray) -> bool:
    return set(np.unique(y_train).tolist()) == set(all_classes.tolist())


def cross_validate_model(X, y, groups: np.ndarray | None) -> dict:
    """GroupKFold cross-validation by capture/session metadata."""
    if groups is None:
        return {
            **_skip_group_validation(
                "Need at least 2 capture_id/session_id groups; random window CV is disabled."
            ),
        }

    unique_groups = np.unique(groups)
    if len(unique_groups) < 2:
        return {
            **_skip_group_validation(
                "Need at least 2 capture_id/session_id groups for GroupKFold."
            ),
        }

    n_splits = min(CV_FOLDS, len(unique_groups))
    all_classes = np.unique(y)
    cv = GroupKFold(n_splits=n_splits)
    scores = []
    skipped_folds = []

    for fold_index, (train_idx, test_idx) in enumerate(
        cv.split(X, y, groups=groups),
        start=1,
    ):
        if not _valid_group_train_split(y[train_idx], all_classes):
            skipped_folds.append({
                "fold": fold_index,
                "reason": "training groups did not include every appliance class",
            })
            continue
        fold_model = train(X[train_idx], y[train_idx])
        score = accuracy_score(y[test_idx], fold_model.predict(X[test_idx]))
        scores.append(float(score))

    if not scores:
        return {
            **_skip_group_validation(
                "No GroupKFold split kept every appliance class in the training fold."
            ),
            "cv_requested_folds": n_splits,
            "cv_skipped_folds": skipped_folds,
        }

    score_array = np.asarray(scores, dtype=float)
    return {
        "cv_mean_accuracy": float(score_array.mean()),
        "cv_std_accuracy": float(score_array.std()),
        "cv_fold_scores": scores,
        "cv_folds": len(scores),
        "cv_requested_folds": n_splits,
        "cv_strategy": "group_kfold",
        "cv_skipped_folds": skipped_folds,
    }


def split_train_test_by_group(
    X,
    y,
    groups: np.ndarray | None,
    class_names: list[str],
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray, np.ndarray | None, bool, dict]:
    """Use the most appliance-diverse valid GroupKFold fold as held-out test."""
    if groups is None:
        reason = "Need capture_id/session_id groups; random window split is disabled."
        print(f"Skipping held-out test split: {reason}")
        return X, None, y, None, False, {
            "test_split_strategy": "group_kfold",
            "test_split_skipped_reason": reason,
        }

    unique_groups = np.unique(groups)
    if len(unique_groups) < 2:
        reason = "Need at least 2 capture_id/session_id groups for GroupKFold."
        print(f"Skipping held-out test split: {reason}")
        return X, None, y, None, False, {
            "test_split_strategy": "group_kfold",
            "test_split_skipped_reason": reason,
        }

    n_splits = min(CV_FOLDS, len(unique_groups))
    all_classes = np.unique(y)
    cv = GroupKFold(n_splits=n_splits)
    skipped_folds = []
    candidates = []

    for fold_index, (train_idx, test_idx) in enumerate(
        cv.split(X, y, groups=groups),
        start=1,
    ):
        if not _valid_group_train_split(y[train_idx], all_classes):
            skipped_folds.append({
                "fold": fold_index,
                "reason": "training groups did not include every appliance class",
            })
            continue
        train_groups = sorted(set(groups[train_idx].tolist()))
        test_groups = sorted(set(groups[test_idx].tolist()))
        test_labels, test_counts = np.unique(y[test_idx], return_counts=True)
        class_distribution = {
            class_names[int(label)]: int(count)
            for label, count in zip(test_labels, test_counts)
        }
        candidates.append({
            "fold": fold_index,
            "train_idx": train_idx,
            "test_idx": test_idx,
            "train_groups": train_groups,
            "test_groups": test_groups,
            "test_class_count": len(test_labels),
            "min_test_class_support": int(test_counts.min()) if len(test_counts) else 0,
            "test_samples": len(test_idx),
            "test_class_distribution": class_distribution,
        })

    if candidates:
        target_test_size = len(y) / n_splits
        best = max(
            candidates,
            key=lambda item: (
                item["test_class_count"],
                item["min_test_class_support"],
                -abs(item["test_samples"] - target_test_size),
            ),
        )
        train_idx = best["train_idx"]
        test_idx = best["test_idx"]
        return (
            X[train_idx],
            X[test_idx],
            y[train_idx],
            y[test_idx],
            True,
            {
                "test_split_strategy": "group_kfold",
                "test_group_count": len(best["test_groups"]),
                "train_group_count": len(best["train_groups"]),
                "test_groups": best["test_groups"],
                "test_group_kfold_fold": best["fold"],
                "test_class_count": best["test_class_count"],
                "test_class_distribution": best["test_class_distribution"],
                "group_kfold_splits": n_splits,
                "skipped_candidate_test_folds": skipped_folds,
            },
        )

    reason = "No GroupKFold split kept every appliance class in the training fold."
    print(f"Skipping held-out test split: {reason}")
    return X, None, y, None, False, {
        "test_split_strategy": "group_kfold",
        "test_split_skipped_reason": reason,
        "group_kfold_splits": n_splits,
        "skipped_candidate_test_folds": skipped_folds,
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
        raw_window_count = len(df)
        df, filtered_inactive_windows = filter_informative_windows(df)
        out = DATA_DIR / "features_extracted.csv"
        df.to_csv(out, index=False)
        print(f"Features saved -> {out}")
    else:
        parser.error("Provide --data or --features")

    if args.features:
        raw_window_count = len(df)
        df, filtered_inactive_windows = filter_informative_windows(df)

    if filtered_inactive_windows:
        print(
            "Filtered inactive windows: "
            f"{filtered_inactive_windows} of {raw_window_count} "
            f"(max_power <= {MIN_ACTIVE_WINDOW_POWER_W} W)"
        )

    if df.empty:
        raise SystemExit("No active feature windows remain after filtering.")

    print(f"\nDataset: {len(df)} windows | {df['appliance_label'].nunique()} classes")
    print(f"Class distribution:\n{df['appliance_label'].value_counts()}\n")

    X, y, le = prepare_data(df)
    group_column, groups = select_group_column(df)
    if group_column:
        print(
            "Group validation: "
            f"{group_column} ({len(np.unique(groups))} groups)"
        )
    else:
        print("Group validation: unavailable (capture_id/session_id missing)")

    X_train, X_test, y_train, y_test, has_test_split, split_metadata = (
        split_train_test_by_group(X, y, groups, le.classes_.tolist())
    )
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

    cv_results = cross_validate_model(X, y, groups)
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
        "feature_set_version": FEATURE_SET_VERSION,
        "feature_policy": (
            "Voltage/current-derived features are excluded from v3 training to "
            "reduce location and sensor-transfer leakage."
        ),
        "removed_feature_cols": REMOVED_FEATURE_COLS,
        "normalized_shape_features": NORMALIZED_SHAPE_FEATURES,
        "raw_feature_windows_before_filter": int(raw_window_count),
        "filtered_inactive_windows": int(filtered_inactive_windows),
        "min_active_window_power_w": MIN_ACTIVE_WINDOW_POWER_W,
        "feature_cols": FEATURE_COLS,
        "top_feature_importance": get_feature_importance(model, FEATURE_COLS),
        "xgb_params": XGB_PARAMS,
        "window_size_s": args.window,
        "group_column": group_column,
        "group_count": int(len(np.unique(groups))) if groups is not None else 0,
        **split_metadata,
        "notes": (
            "This is a smart-plug appliance signature classifier. It is not yet "
            "aggregate household NILM disaggregation. True NILM requires "
            "synchronized main-line aggregate readings plus appliance-level "
            "Tapo labels."
        ),
        **cv_results,
    }
    save_model(model, le, metadata)
    print("\nTraining complete.")


if __name__ == "__main__":
    main()
