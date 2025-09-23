#!/usr/bin/env python3
"""Comprehensive baseline training for NSL-KDD and CIC-IDS-2017 datasets."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


def _print_separator(title: str) -> None:
    print()
    print(title)
    print("=" * len(title))


def train_nsl_kdd_baseline() -> bool:
    """Run the baseline pipeline on the NSL-KDD dataset."""

    _print_separator("🚀 NSL-KDD Baseline Training")

    try:
        from src.preprocessing import NSLKDDAnalyzer, NSLKDDPreprocessor
        from src.models import BaselineModels
    except ImportError as exc:  # pragma: no cover - runtime feedback only
        print(f"❌ Import error: {exc}")
        return False

    try:
        analyzer = NSLKDDAnalyzer()
        train_data = analyzer.load_data("KDDTrain+.txt")
        test_data = analyzer.load_data("KDDTest+.txt")

        if train_data is None or test_data is None:
            print("❌ Training aborted: NSL-KDD data not found.")
            return False

        print("🔄 Preprocessing NSL-KDD data (undersampling for balance)...")
        preprocessor = NSLKDDPreprocessor(balance_method="undersample")
        X_train, X_val, y_train, y_val = preprocessor.fit_transform(train_data)
        X_test, y_test = preprocessor.transform(test_data)

        print("\n🤖 Training baseline models on NSL-KDD...")
        baseline = BaselineModels()
        exclude_models = ["svm_linear"] if len(X_train) > 5_000 else []
        baseline.train_all(X_train, y_train, exclude_models=exclude_models)

        print("\n📊 Validation performance on NSL-KDD...")
        val_results = baseline.evaluate_all(X_val, y_val)
        if val_results.empty:
            print("❌ No baseline models produced validation results for NSL-KDD.")
            return False

        print("\n🏆 NSL-KDD validation leaderboard:")
        print(val_results[["model_name", "accuracy", "f1_score", "precision", "recall"]].round(3))

        best_model_name = val_results.iloc[0]["model_name"]
        print(f"\n🎯 Evaluating best NSL-KDD model ({best_model_name}) on the official test set...")
        test_metrics = baseline.evaluate_model(best_model_name, X_test, y_test)
        for metric in ["accuracy", "f1_score", "precision", "recall"]:
            value = test_metrics.get(metric, float("nan"))
            print(f"   {metric.title():<10}: {value:.3f}")

        print("\n💾 Persisting NSL-KDD baseline artefacts...")
        models_dir = PROJECT_ROOT / "data" / "models" / "baseline"
        results_dir = PROJECT_ROOT / "data" / "results" / "nsl"
        baseline.save_models(str(models_dir), results_dir=str(results_dir), dataset_suffix="_nsl")
        preprocessor.save(str(models_dir / "nsl_preprocessor.pkl"))

        print("✅ NSL-KDD baseline training complete!")
        return True
    except Exception as exc:  # pragma: no cover - runtime feedback only
        print(f"❌ Error during NSL-KDD baseline training: {exc}")
        traceback.print_exc()
        return False


def train_cic_baseline() -> bool:
    """Run the baseline pipeline on the CIC-IDS-2017 dataset using the full data."""

    _print_separator("🚀 CIC-IDS-2017 Baseline Training")

    try:
        from src.preprocessing import CICIDSPreprocessor
        from src.models import BaselineModels
    except ImportError as exc:  # pragma: no cover - runtime feedback only
        print(f"❌ Import error: {exc}")
        return False

    preprocessor = CICIDSPreprocessor()

    try:
        print("📁 Loading full CIC-IDS-2017 dataset...")
        cic_data = preprocessor.load_data(use_full_dataset=True)
        if cic_data is None:
            print("❌ CIC-IDS-2017 data could not be loaded.")
            return False

        print("🔄 Preparing CIC-IDS-2017 features and labels...")
        X_full, y_full = preprocessor.fit_transform(cic_data)

        # Create train/validation/test splits (60/20/20)
        X_train, X_temp, y_train, y_temp = train_test_split(
            X_full,
            y_full,
            test_size=0.4,
            random_state=42,
            stratify=y_full,
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp,
            y_temp,
            test_size=0.5,
            random_state=42,
            stratify=y_temp,
        )

        print("\n🤖 Training baseline models on CIC-IDS-2017...")
        baseline = BaselineModels()
        exclude_models = ["svm_linear", "knn"] if len(X_train) > 10_000 else []
        baseline.train_all(X_train, y_train, exclude_models=exclude_models)

        print("\n📊 Validation performance on CIC-IDS-2017...")
        val_results = baseline.evaluate_all(X_val, y_val)
        if val_results.empty:
            print("❌ No baseline models produced validation results for CIC-IDS-2017.")
            return False

        print("\n🏆 CIC-IDS-2017 validation leaderboard:")
        print(val_results[["model_name", "accuracy", "f1_score", "precision", "recall"]].round(3))

        best_model_name = val_results.iloc[0]["model_name"]
        print(f"\n🎯 Evaluating best CIC baseline model ({best_model_name}) on the hold-out test split...")
        test_metrics = baseline.evaluate_model(best_model_name, X_test, y_test)
        for metric in ["accuracy", "f1_score", "precision", "recall"]:
            value = test_metrics.get(metric, float("nan"))
            print(f"   {metric.title():<10}: {value:.3f}")

        print("\n💾 Persisting CIC-IDS-2017 baseline artefacts...")
        cic_models_dir = PROJECT_ROOT / "data" / "models" / "cic_baseline"
        results_dir = PROJECT_ROOT / "data" / "results" / "cic"
        baseline.save_models(str(cic_models_dir), results_dir=str(results_dir), dataset_suffix="_cic")

        print("✅ CIC-IDS-2017 baseline training complete!")
        return True
    except Exception as exc:  # pragma: no cover - runtime feedback only
        print(f"❌ Error during CIC-IDS-2017 baseline training: {exc}")
        traceback.print_exc()
        return False


def main() -> bool:
    print("🚀 Baseline Training Pipeline")
    print("=" * 60)

    success_nsl = train_nsl_kdd_baseline()
    success_cic = train_cic_baseline()

    print("\n" + "=" * 60)
    if success_nsl and success_cic:
        print("✅ Baseline training completed for both NSL-KDD and CIC-IDS-2017!")
    elif success_nsl:
        print("⚠️ Baseline training completed for NSL-KDD only.")
    elif success_cic:
        print("⚠️ Baseline training completed for CIC-IDS-2017 only.")
    else:
        print("❌ Baseline training failed for all datasets.")

    return success_nsl and success_cic


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
