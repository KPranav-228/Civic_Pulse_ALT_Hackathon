"""Tests for Phase 1: Real dataset collection, conversion, and high-severity evaluation."""

import json
from pathlib import Path
import pytest

from server.nlp.classifiers import model_suite
from server.scripts.collect_real_data import convert_csv_to_json, create_template_csv
from server.scripts.evaluate_synthetic_vs_real import evaluate_split


def test_collect_real_data_workflow(tmp_path):
    """Test generating a template CSV and converting it to schema-compatible JSON."""
    csv_path = tmp_path / "test_announcements.csv"
    json_path = tmp_path / "test_announcements.json"

    # 1. Create template
    create_template_csv(csv_path)
    assert csv_path.exists()

    # 2. Convert to JSON
    records = convert_csv_to_json(csv_path, json_path)
    assert json_path.exists()
    assert len(records) == 2
    assert records[0]["category"] in {"water_supply", "road_closure"}
    assert records[0]["source_tier"] == "official"


def test_high_severity_metrics_computation():
    """Verify high-severity precision/recall calculation logic."""
    y_true = ["critical", "warning", "info", "advisory", "critical"]
    y_pred = ["critical", "warning", "warning", "info", "critical"]

    metrics = model_suite.compute_high_severity_metrics(y_true, y_pred)
    assert "high_severity_precision" in metrics
    assert "critical_precision" in metrics
    assert "warning_recall" in metrics

    # 3 predictions are in {critical, warning}, of which 2 are truly in {critical, warning}
    # y_pred[0]=crit(T), y_pred[1]=warn(T), y_pred[2]=warn(F-true is info), y_pred[4]=crit(T)
    # Actually: y_pred high_sev = indices 0 (crit), 1 (warn), 2 (warn), 4 (crit) -> 4 predicted high
    # True for these: index 0 (crit-yes), 1 (warn-yes), 2 (info-no), 4 (crit-yes) -> 3/4 = 0.75
    assert metrics["high_severity_precision"] == 0.75
    assert metrics["critical_precision"] == 1.0


def test_synthetic_vs_real_graceful_handling():
    """Verify evaluate_split handles both populated and empty datasets safely."""
    # Empty dataset
    empty_res = evaluate_split([], "Empty Test Set")
    assert empty_res["samples"] == 0
    assert empty_res["high_severity_precision"] is None

    # Populated mock dataset
    sample = [
        {"text": "Severe power disruption in Begumpet.", "category": "power_cut", "severity": "critical", "is_spam": False},
        {"text": "Planned pipeline repair in Madhapur.", "category": "water_supply", "severity": "advisory", "is_spam": False},
    ]
    model_suite.load_artifacts()
    res = evaluate_split(sample, "Mock Split")
    assert res["samples"] == 2
    assert res["cat_accuracy"] is not None
    assert res["high_severity_precision"] is not None


def test_metadata_has_high_severity_precision():
    """Verify server/models/metadata.json records high_severity_precision."""
    meta_path = Path("server/models/metadata.json")
    assert meta_path.exists()
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert "high_severity_precision" in meta
    assert isinstance(meta["high_severity_precision"], (int, float))
    assert 0.0 <= meta["high_severity_precision"] <= 1.0
