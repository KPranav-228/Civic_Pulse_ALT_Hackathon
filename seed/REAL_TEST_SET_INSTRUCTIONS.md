# Real-World Hyderabad Municipal Test Set Instructions

This file documents the schema and ingestion process for real municipal announcements collected from official Hyderabad agencies:
- **GHMC** (Greater Hyderabad Municipal Corporation)
- **HMWSSB** (Hyderabad Metropolitan Water Supply and Sewerage Board)
- **TGSPDCL** (Telangana Southern Power Distribution Company Limited)
- **Hyderabad Traffic Police** (HYDTP)

## Required JSON Schema per Item

Each item in `seed/real_test_set.json` must adhere to the following schema:

```json
{
  "id": 1,
  "text": "Full announcement text as released by the official agency or news source.",
  "category": "road_closure | water_supply | power_cut | severe_weather | public_service | other",
  "severity": "critical | warning | advisory | info",
  "is_spam": false,
  "affected_area": "Locality name matching Hyderabad gazetteer (e.g., Gachibowli, Begumpet)",
  "source_name": "Official Agency or Publisher name (e.g. TGSPDCL, HMWSSB)",
  "source_url": "https://official-portal-or-tweet-link",
  "source_tier": "official | news | unverified",
  "published_at": "2026-10-26T10:00:00Z",
  "is_code_mixed": false
}
```

## How to Collect & Convert Real Data

1. Generate a blank CSV template or fill in `data/real_announcements.csv`:
   ```bash
   python server/scripts/collect_real_data.py --template
   ```
2. Manually paste real announcements into the CSV and label `category`, `severity`, `source_name`, `source_url`, and `affected_area`.
3. Convert the CSV into the validated `seed/real_test_set.json`:
   ```bash
   python server/scripts/collect_real_data.py --csv data/real_announcements.csv --out seed/real_test_set.json
   ```
4. Run the synthetic vs. real evaluation:
   ```bash
   python server/scripts/evaluate_synthetic_vs_real.py
   ```
