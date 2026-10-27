# Dataset Card: CivicPulse Synthetic Urban Alerts (CPSUA-665)

## 1. Dataset Summary
- **Dataset Name:** CivicPulse Synthetic Urban Alerts (`seed_data.json`)
- **Version:** 1.0.0 (Reproducible Seed `42`)
- **Creation Date:** October 2026
- **Total Records:** 665
- **Languages:** English, Transliterated Indian English (Telugu/Hindi code-mixed)
- **Primary Tasks:**
  1. Binary Spam / Irrelevant Report Filtering (`is_spam`)
  2. Multi-class Alert Category Classification (6 categories)
  3. Multi-class Urgency / Severity Classification (4 levels)
  4. Topic Modeling & Deduplication Clustering
  5. Named Entity Recognition (Locations, Facilities, Organizations)

---

## 2. Category & Severity Distribution

| Category | Count | Primary Focus |
|---|---|---|
| `road_closure` | 112 | Lane blockades, flyover repairs, culvert collapse, diversions |
| `water_supply` | 103 | Pipeline ruptures, contaminated supply advisories, desilting |
| `power_cut` | 104 | Feeder maintenance, transformer trips, rolling load shedding |
| `severe_weather`| 102 | Thunderstorms, urban flooding, heatwaves, dense fog, AQI alerts |
| `public_service`| 104 | School closures, transit bus re-routings, pulse polio drives |
| `other` (Civic) | 70 | Municipal hearings, heritage festivals, vaccination camps |
| `spam` (Irrelevant)| 70 | Real estate clickbait, lottery scams, commercial promotions |
| `code_mixed` | 15 | Transliterated Hindi / Telugu civic notices |

### Severity Class Distribution
- **`info`** (245): Non-urgent advisories, tax camps, routine civic events, filtered spam.
- **`advisory`** (185): Planned supply interruptions, scheduled prunings, minor delays.
- **`warning`** (176): Severe thunderstorm alerts, major pipe bursts, road diversions.
- **`critical`** (59): Flash flood warnings, collapsed culverts, hospital emergency notices.

---

## 3. Data Generation & Noise Injection Methodology
The dataset was produced using template permutations parameterized across 4 Indian metropolitan areas (Hyderabad, Bengaluru, Chennai, Delhi NCR), incorporating authentic street names, landmarks, and utility authorities.

### Injected Realistic Noise (~12% rate across non-spam items):
1. **Typographical Errors:** Adjacent character transposition in middle tokens (e.g., `flodyver`, `resuriacfing`).
2. **Standard Abbreviations:** `Rd.` for `Road`, `St.` for `Street`, `Govt` for `Government`, `Dept` for `Department`.
3. **Format Inconsistencies:** Date styles ranging from `DD/MM/YYYY` to conversational `tomorrow` or `next Monday`.
4. **Casing Irregularities:** Capitalized headlines and exclamation marks mimicking real-time emergency broadcasts.

---

## 4. Train / Validation / Test Splits

The dataset is partitioned deterministically using a 70% / 15% / 15% ratio with `RANDOM_SEED = 42`:
- **`train.json`:** 465 records
- **`val.json`:** 99 records
- **`test.json`:** 101 records

---

## 5. Known Limitations & Ethical Considerations
- **Synthetic Origin:** While modeled after real GHMC, BWSSB, and traffic police notifications, synthetic phrases have lower linguistic variance than open-web scraping.
- **Geographic Bias:** Geographic entities focus on Southern and Central Indian urban centers.
- **Safety Criticality:** As disclaimed throughout CivicPulse, automated alerts must be verified against official civic portals before high-risk decisions are made.
