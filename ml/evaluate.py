"""
Evaluation script for trained NeuralWatt NILM classifier.

Outputs:
    results/confusion_matrix.csv
    results/classification_report.txt
    results/eval_summary.json

Usage:
    python evaluate.py --model models/nilm_v1.pkl --data data/sample_appliance_data.csv
    python evaluate.py --model models/nilm_v1.pkl --features data/features_extracted.csv
"""

import argparse
import pickle
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import GroupKFold

try:
    from .feature_extraction import load_and_extract
except ImportError:
    from feature_extraction import load_and_extract

RESULTS_DIR = Path(__file__).parent / "results"
CV_FOLDS = 5
GROUP_COLUMNS = ("capture_id", "session_id")


def load_model(model_path: str) -> dict:
    """Load serialized model artifact."""
    with open(model_path, "rb") as f:
        artifact = pickle.load(f)
    required = {"model", "label_encoder", "feature_cols"}
    missing = required - set(artifact.keys())
    if missing:
        raise ValueError(f"Model artifact missing keys: {missing}")
    return artifact


def load_features(path: str, feature_cols: list) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = set(feature_cols + ["appliance_label"]) - set(df.columns)
    if missing:
        raise ValueError(f"Feature CSV missing columns: {missing}")
    return df


def evaluate(artifact: dict, df: pd.DataFrame) -> dict:
    """Run full evaluation and return results dict."""
    model = artifact["model"]
    le = artifact["label_encoder"]
    feature_cols = artifact["feature_cols"]

    X = df[feature_cols].values
    y_true_enc = le.transform(df["appliance_label"].values)
    y_pred_enc = model.predict(X)

    y_true = le.inverse_transform(y_true_enc)
    y_pred = le.inverse_transform(y_pred_enc)

    acc = accuracy_score(y_true, y_pred)
    report_text = classification_report(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=le.classes_)

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=le.classes_, average=None, zero_division=0
    )

    per_class = {}
    for i, cls in enumerate(le.classes_):
        per_class[cls] = {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
        }

    return {
        "accuracy": float(acc),
        "per_class": per_class,
        "classification_report_text": report_text,
        "confusion_matrix": cm.tolist(),
        "class_labels": le.classes_.tolist(),
    }


def save_results(results: dict, output_dir: Path):
    """Write confusion matrix CSV, report text, and summary JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    cm_df = pd.DataFrame(
        results["confusion_matrix"],
        index=results["class_labels"],
        columns=results["class_labels"],
    )
    cm_path = output_dir / "confusion_matrix.csv"
    cm_df.to_csv(cm_path)
    print(f"Confusion matrix -> {cm_path}")

    report_path = output_dir / "classification_report.txt"
    with open(report_path, "w") as f:
        f.write(results["classification_report_text"])
    print(f"Classification report -> {report_path}")

    summary = {k: v for k, v in results.items() if k != "classification_report_text"}
    summary_path = output_dir / "eval_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Eval summary -> {summary_path}")


def print_summary(results: dict):
    print("\n" + "=" * 54)
    print(f"  Overall Accuracy: {results['accuracy']:.4f}  ({results['accuracy']*100:.1f}%)")
    print("=" * 54)
    print(f"\n{'Appliance':<22} {'Precision':>9} {'Recall':>8} {'F1':>6} {'Support':>8}")
    print("-" * 56)
    for cls, m in results["per_class"].items():
        print(
            f"  {cls:<20} {m['precision']:>9.2f} {m['recall']:>8.2f} "
            f"{m['f1']:>6.2f} {m['support']:>8}"
        )
    print("\n" + results["classification_report_text"])


def _clean_groups(df: pd.DataFrame, column: str) -> pd.Series:
    groups = (
        df[column]
        .astype("string")
        .fillna("")
        .str.strip()
    )
    return groups.mask(groups == "", "__missing_group__")


def select_group_column(df: pd.DataFrame, preferred: str | None = None) -> tuple[str | None, pd.Series | None]:
    """Choose capture/session metadata for group-aware evaluation."""
    candidates = [preferred] if preferred else []
    candidates.extend(column for column in GROUP_COLUMNS if column not in candidates)

    for column in candidates:
        if not column or column not in df.columns:
            continue
        groups = _clean_groups(df, column)
        if int(groups.nunique()) >= 2:
            return column, groups
    return None, None


def _metadata_test_groups(metadata: dict) -> tuple[str | None, set[str]]:
    group_column = metadata.get("group_column")
    test_groups = metadata.get("test_groups", [])
    return group_column, {str(group) for group in test_groups}


def select_eval_data(df: pd.DataFrame, metadata: dict) -> tuple[pd.DataFrame, bool, dict]:
    """Use model test groups or a GroupKFold fold; never random window splits."""
    metadata_group_column, metadata_groups = _metadata_test_groups(metadata)
    if metadata_group_column and metadata_groups and metadata_group_column in df.columns:
        groups = _clean_groups(df, metadata_group_column)
        mask = groups.isin(metadata_groups)
        if bool(mask.any()):
            return df.loc[mask].reset_index(drop=True), True, {
                "eval_split_strategy": "metadata_test_groups",
                "eval_group_column": metadata_group_column,
                "eval_group_count": int(groups[mask].nunique()),
            }

    group_column, groups = select_group_column(df, metadata_group_column)
    if groups is None:
        reason = "Need capture_id/session_id groups; random window evaluation is disabled."
        print(f"Skipping held-out split: {reason}")
        return df, False, {
            "eval_split_strategy": "available_rows",
            "eval_split_skipped_reason": reason,
        }

    unique_groups = groups.unique()
    if len(unique_groups) < 2:
        reason = "Need at least 2 capture_id/session_id groups for GroupKFold."
        print(f"Skipping held-out split: {reason}")
        return df, False, {
            "eval_split_strategy": "available_rows",
            "eval_split_skipped_reason": reason,
        }

    labels = df["appliance_label"].to_numpy()
    all_classes = set(pd.unique(labels).tolist())
    n_splits = min(CV_FOLDS, len(unique_groups))
    cv = GroupKFold(n_splits=n_splits)

    for fold_index, (train_idx, test_idx) in enumerate(
        cv.split(df, labels, groups=groups.to_numpy(dtype=str)),
        start=1,
    ):
        if set(pd.unique(labels[train_idx]).tolist()) != all_classes:
            continue
        return df.iloc[test_idx].reset_index(drop=True), True, {
            "eval_split_strategy": "group_kfold",
            "eval_group_column": group_column,
            "eval_group_count": int(groups.iloc[test_idx].nunique()),
            "eval_group_kfold_splits": n_splits,
            "eval_fold": fold_index,
        }

    reason = "No GroupKFold split kept every appliance class in the training side."
    print(f"Skipping held-out split: {reason}")
    return df, False, {
        "eval_split_strategy": "available_rows",
        "eval_split_skipped_reason": reason,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate NeuralWatt NILM classifier")
    parser.add_argument("--model", required=True, help="Path to nilm_v1.pkl")
    parser.add_argument("--data", help="Path to raw appliance CSV")
    parser.add_argument("--features", help="Path to pre-extracted features CSV")
    parser.add_argument("--window", type=int, default=30)
    parser.add_argument("--output", default=str(RESULTS_DIR))
    args = parser.parse_args()

    artifact = load_model(args.model)
    feature_cols = artifact["feature_cols"]

    if args.features:
        df = load_features(args.features, feature_cols)
    elif args.data:
        df = load_and_extract(args.data, window_size=args.window)
    else:
        parser.error("Provide --data or --features")

    metadata = artifact.get("metadata") or {}
    df_test, used_held_out_split, split_metadata = select_eval_data(df, metadata)
    split_label = "group-held-out test" if used_held_out_split else "available"
    print(f"Evaluating on {len(df_test)} {split_label} windows")

    results = evaluate(artifact, df_test)
    results["used_held_out_split"] = used_held_out_split
    results.update(split_metadata)
    print_summary(results)
    save_results(results, Path(args.output))


if __name__ == "__main__":
    main()
