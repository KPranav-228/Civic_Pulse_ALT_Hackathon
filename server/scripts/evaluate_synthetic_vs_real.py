"""Evaluation script: Train on synthetic data and test on real Hyderabad announcements.

Outputs comparison table reports/comparison_tables/synthetic_vs_real.csv and records
high-severity precision metrics in server/models/metadata.json.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.nlp.classifiers import model_suite
from server.nlp.preprocess import default_preprocessor

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("evaluate_synthetic_vs_real")


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    """Load JSON dataset if present and valid."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Failed to parse {path}: {e}")
            return []


def evaluate_split(
    items: List[Dict[str, Any]],
    dataset_name: str
) -> Dict[str, Any]:
    """Run category and severity inference on an item list and return evaluation metrics."""
    if not items:
        return {
            "dataset": dataset_name,
            "samples": 0,
            "status": "No data supplied (file is empty)",
            "cat_accuracy": None,
            "cat_f1_macro": None,
            "sev_accuracy": None,
            "sev_f1_macro": None,
            "high_severity_precision": None,
            "critical_f1": None,
            "warning_f1": None,
        }

    # Filter non-spam items for category/severity evaluation
    eval_items = [d for d in items if not d.get("is_spam", False)]
    if not eval_items:
        eval_items = items

    y_cat_true = [d["category"] for d in eval_items]
    y_sev_true = [d["severity"] for d in eval_items]

    y_cat_pred = []
    y_sev_pred = []

    for d in eval_items:
        pred = model_suite.predict(d["text"])
        y_cat_pred.append(pred["category"])
        y_sev_pred.append(pred["severity"])

    cat_acc = accuracy_score(y_cat_true, y_cat_pred)
    cat_f1 = f1_score(y_cat_true, y_cat_pred, average="macro", zero_division=0)
    sev_acc = accuracy_score(y_sev_true, y_sev_pred)
    sev_f1 = f1_score(y_sev_true, y_sev_pred, average="macro", zero_division=0)

    # High severity metrics
    high_sev_metrics = model_suite.compute_high_severity_metrics(y_sev_true, y_sev_pred)

    return {
        "dataset": dataset_name,
        "samples": len(eval_items),
        "status": "Evaluated",
        "cat_accuracy": round(float(cat_acc), 4),
        "cat_f1_macro": round(float(cat_f1), 4),
        "sev_accuracy": round(float(sev_acc), 4),
        "sev_f1_macro": round(float(sev_f1), 4),
        "high_severity_precision": high_sev_metrics["high_severity_precision"],
        "critical_f1": high_sev_metrics["critical_f1"],
        "warning_f1": high_sev_metrics["warning_f1"],
    }


def main():
    train_file = PROJECT_ROOT / "seed" / "train.json"
    test_file = PROJECT_ROOT / "seed" / "test.json"
    real_file = PROJECT_ROOT / "seed" / "real_test_set.json"
    reports_dir = PROJECT_ROOT / "reports" / "comparison_tables"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ensure models loaded or train if needed
    if not model_suite.load_artifacts():
        logger.info("Artifacts missing, training model suite on synthetic seed...")
        seed_master = PROJECT_ROOT / "seed" / "seed_data.json"
        model_suite.train_suite(seed_master, reports_dir=PROJECT_ROOT / "reports")

    # 2. Evaluate synthetic test set
    syn_test_data = load_dataset(test_file)
    logger.info(f"Evaluating on synthetic test set ({len(syn_test_data)} items)...")
    syn_results = evaluate_split(syn_test_data, "Synthetic Test Set (seed/test.json)")

    # 3. Evaluate real test set
    real_test_data = load_dataset(real_file)
    logger.info(f"Checking real test set ({len(real_test_data)} items)...")
    real_results = evaluate_split(real_test_data, "Real Announcements (seed/real_test_set.json)")

    # 4. Combine into comparison dataframe
    df = pd.DataFrame([syn_results, real_results])

    csv_path = reports_dir / "synthetic_vs_real.csv"
    md_path = reports_dir / "synthetic_vs_real.md"

    df.to_csv(csv_path, index=False)
    df.to_markdown(md_path, index=False)
    logger.info(f"Saved evaluation comparison to:\n - {csv_path}\n - {md_path}")

    # 5. Update metadata.json with the high_severity_metrics
    meta_path = PROJECT_ROOT / "server" / "models" / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["high_severity_precision"] = syn_results["high_severity_precision"]
        meta["synthetic_test_metrics"] = syn_results
        if real_test_data:
            meta["real_test_metrics"] = real_results
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Updated {meta_path} with high-severity precision: {syn_results['high_severity_precision']}")

    print("\n--- Evaluation Summary: Synthetic vs Real Data ---")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
