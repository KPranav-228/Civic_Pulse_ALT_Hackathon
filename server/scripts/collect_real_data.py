"""Manual data collection and labeling pipeline for real Hyderabad civic announcements.

Supports CSV-to-JSON conversion with strict schema validation for official agency feeds:
GHMC, HMWSSB, TGSPDCL, and Hyderabad Traffic Police.
"""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("collect_real_data")

VALID_CATEGORIES = {
    "road_closure",
    "water_supply",
    "power_cut",
    "severe_weather",
    "public_service",
    "other",
}

VALID_SEVERITIES = {"critical", "warning", "advisory", "info"}
VALID_SOURCE_TIERS = {"official", "news", "unverified"}


def create_template_csv(target_path: Path):
    """Generate a starter CSV template with column definitions and sample instructions."""
    fieldnames = [
        "text",
        "category",
        "severity",
        "is_spam",
        "affected_area",
        "source_name",
        "source_url",
        "source_tier",
        "published_at",
        "is_code_mixed",
    ]
    sample_rows = [
        {
            "text": "Emergency pipeline maintenance near Cyber Towers underpass. Water supply disrupted for 12 hours.",
            "category": "water_supply",
            "severity": "warning",
            "is_spam": "false",
            "affected_area": "Madhapur",
            "source_name": "HMWSSB",
            "source_url": "https://twitter.com/HMWSSBOnline/status/123456",
            "source_tier": "official",
            "published_at": "2026-10-26T09:00:00Z",
            "is_code_mixed": "false",
        },
        {
            "text": "Traffic advisory: Waterlogging reported near Begumpet flyover. Vehicles diverted via Greenlands.",
            "category": "road_closure",
            "severity": "critical",
            "is_spam": "false",
            "affected_area": "Begumpet",
            "source_name": "Hyderabad Traffic Police",
            "source_url": "https://twitter.com/HYDTP/status/789012",
            "source_tier": "official",
            "published_at": "2026-10-26T10:30:00Z",
            "is_code_mixed": "false",
        },
    ]

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_rows)

    logger.info(f"Sample template CSV written to: {target_path}")


def convert_csv_to_json(csv_path: Path, output_json: Path) -> List[Dict[str, Any]]:
    """Read a manually labeled CSV, validate every record, and save schema-compatible JSON."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    records = []
    errors = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=1):
            text = (row.get("text") or "").strip()
            if not text:
                continue

            category = (row.get("category") or "other").strip().lower()
            if category not in VALID_CATEGORIES:
                errors.append(f"Row {row_idx}: Invalid category '{category}'. Must be one of {VALID_CATEGORIES}")

            severity = (row.get("severity") or "info").strip().lower()
            if severity not in VALID_SEVERITIES:
                errors.append(f"Row {row_idx}: Invalid severity '{severity}'. Must be one of {VALID_SEVERITIES}")

            is_spam = str(row.get("is_spam", "false")).strip().lower() in {"true", "1", "yes"}
            source_tier = (row.get("source_tier") or "unverified").strip().lower()
            if source_tier not in VALID_SOURCE_TIERS:
                source_tier = "unverified"

            is_code_mixed = str(row.get("is_code_mixed", "false")).strip().lower() in {"true", "1", "yes"}

            item = {
                "id": len(records) + 1,
                "text": text,
                "category": category,
                "severity": severity,
                "is_spam": is_spam,
                "affected_area": (row.get("affected_area") or "Hyderabad General").strip(),
                "source_name": (row.get("source_name") or "Municipal Notice").strip(),
                "source_url": (row.get("source_url") or "").strip() or None,
                "source_tier": source_tier,
                "published_at": (row.get("published_at") or "").strip() or None,
                "is_code_mixed": is_code_mixed,
            }
            records.append(item)

    if errors:
        for err in errors[:10]:
            logger.warning(err)
        if len(errors) > 10:
            logger.warning(f"... and {len(errors) - 10} more validation errors.")

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully converted {len(records)} records from {csv_path} -> {output_json}")
    return records


def main():
    parser = argparse.ArgumentParser(description="Collect and validate real Hyderabad civic announcements.")
    parser.add_argument("--template", type=str, help="Generate a blank CSV template at the specified path.")
    parser.add_argument("--csv", type=str, help="Path to labeled CSV input file.")
    parser.add_argument("--out", type=str, default="seed/real_test_set.json", help="Destination JSON path.")

    args = parser.parse_args()

    if args.template:
        create_template_csv(Path(args.template))
        return

    if args.csv:
        convert_csv_to_json(Path(args.csv), Path(args.out))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
