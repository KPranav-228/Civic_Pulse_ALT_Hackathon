"""Feedback Merging & Active Retraining Script for CivicPulse.

Extracts unmerged citizen corrections from the database, converts them
into labeled training instances, merges them into the active training set,
and marks corrections as processed.

Usage:
    python -m server.scripts.merge_feedback [--retrain]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.db.database import SessionLocal, init_db
from server.db import crud
from server.nlp.classifiers import model_suite

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("merge_feedback")


def merge_citizen_corrections(
    output_file: Path = PROJECT_ROOT / "seed" / "seed_data.json",
    retrain: bool = False
) -> int:
    """Merge unmerged citizen corrections into the training dataset."""
    init_db()
    db = SessionLocal()

    try:
        corrections = crud.get_unmerged_corrections(db)
        if not corrections:
            logger.info("No unmerged corrections found in database. Training data is up to date.")
            return 0

        logger.info(f"Found {len(corrections)} unmerged citizen corrections.")

        # Load existing seed data
        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                seed_data = json.load(f)
        else:
            seed_data = []

        new_samples = []
        merged_ids = []

        for corr in corrections:
            alert = corr.alert
            if not alert:
                continue

            # Determine corrected label
            final_cat = corr.suggested_category or alert.category
            final_sev = corr.suggested_severity or alert.severity

            # Extract area name
            area_name = "Hyderabad"
            if alert.affected_areas:
                try:
                    areas = json.loads(alert.affected_areas)
                    if areas and isinstance(areas, list):
                        area_name = areas[0].get("name", "Hyderabad")
                except Exception:
                    pass

            sample = {
                "text": alert.title,
                "category": final_cat,
                "severity": final_sev,
                "affected_area": area_name,
                "source_name": f"Citizen Verified ({alert.source_name or 'Public'})",
                "is_spam": False,
                "user_corrected": True,
                "feedback_comment": corr.comment
            }
            new_samples.append(sample)
            merged_ids.append(corr.id)

        # Append new samples and save
        seed_data.extend(new_samples)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(seed_data, f, indent=2, ensure_ascii=False)

        # Mark corrections as merged in database
        crud.mark_corrections_merged(db, merged_ids)
        logger.info(f"Successfully merged {len(new_samples)} corrected samples into {output_file}.")

        if retrain:
            logger.info("Triggering suite retraining on augmented dataset...")
            model_suite.train_suite(output_file)
            logger.info("Retraining complete. New models saved to server/models/.")

        return len(new_samples)

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Merge citizen feedback corrections into training set.")
    parser.add_argument("--retrain", action="store_true", help="Trigger classifier retraining after merge.")
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "seed" / "seed_data.json"), help="Output path for dataset.")
    args = parser.parse_args()

    count = merge_citizen_corrections(output_file=Path(args.output), retrain=args.retrain)
    print(f"Merge process completed: {count} samples processed.")


if __name__ == "__main__":
    main()
