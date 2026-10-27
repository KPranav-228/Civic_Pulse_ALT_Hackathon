"""Synthetic Dataset Generator for CivicPulse.

Generates 650+ realistic local news reports, official municipal announcements,
and public utility alerts with realistic noise, Indian city locations,
and code-mixed transliterated samples.
"""

import json
import random
import re
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Fixed random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

OUTPUT_DIR = Path(__file__).resolve().parent

# Indian cities and neighborhoods
AREAS = {
    "Hyderabad": [
        "Begumpet", "Ameerpet", "Hitec City", "Madhapur", "Gachibowli",
        "Kukatpally", "Banjara Hills", "Jubilee Hills", "Secunderabad",
        "Charminar", "Dilsukhnagar", "Mehdipatnam", "Uppal", "Miyapur"
    ],
    "Bengaluru": [
        "Indiranagar", "Koramangala", "Whitefield", "HSR Layout", "Electronic City",
        "Jayanagar", "Marathahalli", "Hebbal", "Malleshwaram", "BTM Layout",
        "Bellandur", "MG Road", "Yelahanka", "Rajajinagar"
    ],
    "Chennai": [
        "T. Nagar", "Adyar", "Velachery", "Anna Nagar", "Mylapore",
        "Guindy", "OMR", "Tambaram", "Besant Nagar", "Nungambakkam"
    ],
    "Delhi NCR": [
        "Connaught Place", "Lajpat Nagar", "Rohini", "Dwarka", "Saket",
        "Karol Bagh", "Noida Sector 62", "Cyber City Gurugram", "Vasant Kunj"
    ]
}

ALL_AREAS = [area for city_areas in AREAS.values() for area in city_areas]

SOURCES = {
    "official": [
        "GHMC Disaster Response", "Traffic Police Department", "State Electricity Board",
        "Metropolitan Water Supply & Sewerage Board", "Municipal Corporation Advisory",
        "District Collectorate", "Fire and Rescue Services", "State Meteorological Dept",
        "Public Transport Corporation", "Urban Development Authority"
    ],
    "news": [
        "City Express", "Deccan Herald", "The Hindu Local", "Metro Mirror",
        "Regional Daily", "Urban News Network", "Civic Watch Journal", "Times Local Feed"
    ]
}

ROAD_TEMPLATES = [
    "Traffic movement will be restricted along {road} due to flyover construction work between {time1} and {time2}. Commuters traveling toward {area} are advised to take alternative detours via {alt_route}.",
    "Emergency repair of a collapsed culvert near {landmark} has blocked all four lanes on {road}. Vehicles heading from {area} are being diverted through {alt_route}. Heavy congestion reported.",
    "Road widening and asphalt resurfacing operations scheduled on {road} starting {date}. Lane closures will remain in effect until {end_date}. Expect delays of 25-40 minutes.",
    "Major waterlogging under the {area} railway underpass has completely halted vehicular traffic. Civic teams are pumping out water. Avoid {road} and use {alt_route} instead.",
    "Due to the upcoming annual marathon, vehicular movement on {road} passing through {area} will be fully suspended from {time1} to {time2}. Emergency services remain exempted.",
    "A multi-vehicle pileup near {landmark} in {area} has blocked the outbound carriageway. Towing operations are underway; police advise avoiding {road} for the next 2 hours.",
    "Metro rail girder installation work will cause overnight road blockades on {road} between {time1} and {time2}. Commuters bound for {area} should plan detours.",
    "Sinkhole reported near {landmark} on {road}. Police barricades have been erected restricting heavy vehicles. Light motor vehicles diverted via {alt_route} in {area}.",
    "Traffic alert: VIP convoy movement scheduled through {area} between {time1} and {time2}. Expect intermittent halts on {road} and adjoining arterial junctions.",
    "Gas pipeline laying work underway across {road} near {area}. One-way traffic system enforced until {date}. Follow directional signages strictly."
]

WATER_TEMPLATES = [
    "Water supply will be completely interrupted in {area} and surrounding sectors for 24 hours on {date} due to urgent maintenance work on the main pumping line at {landmark}.",
    "A major pipeline rupture near {landmark} has caused low pressure and muddy water supply across {area}. Tanker assistance has been arranged by the water board.",
    "Routine desilting and tank cleaning at {landmark} reservoir will disrupt drinking water supply in {area} from {time1} to {time2}. Residents are urged to store adequate water.",
    "Contamination detected in overhead reservoir line feeding {area}. Boiling water advisory issued for all domestic consumers until laboratory clearance on {date}.",
    "Scheduled electrical grid repair at the {area} water treatment plant will lead to zero supply on {date}. Emergency water helpline: 1916.",
    "Low pressure alert: Valve replacement work in {area} will reduce municipal tap water supply by 50% between {time1} and {time2}.",
    "Sewerage overflow repair near {landmark} requires temporary suspension of drinking water supply in {area} to prevent cross-contamination. Restoration expected by {time2}.",
    "Raw water pump station breakdown due to upstream debris. Water distribution to {area} will be deferred by 12 hours starting {time1}."
]

POWER_TEMPLATES = [
    "Scheduled feeder maintenance will cause power supply interruption in {area} on {date} from {time1} to {time2}. Affected sections include {landmark} and adjacent colonies.",
    "A 33kV distribution transformer caught fire near {landmark} causing sudden blackout across {area}. Repair crews dispatched; estimated restoration time is {duration}.",
    "Urgent vegetation pruning along overhead high-tension lines in {area} requires scheduled power outage on {date} between {time1} and {time2}.",
    "Unscheduled power trip reported across {area} following high-voltage grid fluctuation. Technical teams investigating sub-station near {landmark}.",
    "Load shedding notice: Peak summer demand requires rolling 2-hour rotational power cuts in {area} between {time1} and {time2} daily until {date}.",
    "Underground power cable damage during road digging work has cut electricity to {area}. Technicians on site; power expected to resume by {time2}.",
    "Sub-station upgrade works in {area} will necessitate supply suspension to commercial and residential consumers on {date} from {time1} to {time2}."
]

WEATHER_TEMPLATES = [
    "Red alert issued for {area} and adjoining districts: Extremely heavy rainfall exceeding 180mm forecast over next 24 hours. Possibility of localized flooding and tree fall.",
    "Severe thunderstorm accompanied by gusty winds up to 65 kmph and hail expected across {area} between {time1} and {time2}. Stay indoors and away from electrical poles.",
    "Heatwave alert: Maximum temperatures projected to cross 44.5 degrees Celsius in {area} over the next 3 days. Orange alert sounded by meteorological center.",
    "Dense fog advisory: Visibility dropped below 50 meters near {landmark} and across {area}. Highway commuters warned to use hazard lights and reduce speed.",
    "Urban flash flood warning: Rising water levels in storm drains around {area}. Inundation expected in low-lying localities near {landmark}. SDRF deployed on standby.",
    "Air Quality Index (AQI) plunged to 'Severe' category (412) in {area}. Schools advised to suspend outdoor morning assemblies. Vulnerable citizens should wear N95 masks."
]

PUBLIC_SERVICE_TEMPLATES = [
    "All government and private schools in {area} will remain closed on {date} due to administrative directions following heavy rainfall alerts.",
    "Metro train services on the corridor connecting {area} to {landmark} will run with 15-minute headway instead of 5 minutes due to signaling software migration.",
    "Special pulse polio immunization drive scheduled in {area} on {date}. Primary health centers and mobile booths near {landmark} will operate from {time1} to {time2}.",
    "Garbage collection services in {area} will be delayed by one day due to sanitation workers' training workshop on {date}.",
    "Municipal property tax collection facilitation camp to be set up at Community Hall near {landmark} in {area} on {date} from {time1} to {time2}.",
    "Public transport bus route 47B connecting {area} to central station re-routed via {alt_route} effective {date} owing to ongoing construction.",
    "Civil registration and Aadhaar enrollment center in {area} shifted temporarily to District Complex near {landmark} starting {date}."
]

OTHER_TEMPLATES = [
    "Public consultation meeting regarding the new master plan for {area} will be conducted at town hall on {date} at {time1}. Citizens invited to submit representations.",
    "Annual heritage walk and cultural festival in {area} will take place this weekend. Expect pedestrian crowds and limited street parking near {landmark}.",
    "Civic census and house listing enumeration teams will visit residential societies in {area} starting {date}. Residents requested to cooperate with ID-card holders.",
    "Anti-rabies vaccination and stray animal sterilization camp organized by municipal corporation in {area} on {date} near {landmark}.",
    "Notice of auction of unclaimed municipal land parcels in {area} scheduled for {date}. Interested bidders may inspect documents at the ward office."
]

SPAM_TEMPLATES = [
    "HURRY! Mega clearance sale at Grand Mall near {area}! Flat 70% off on all luxury apparel and electronics this weekend only! Click bit.ly/mega-deal now!",
    "Earn 50,000 INR per week working from home! No experience needed for data entry in {area}. WhatsApp your resume to 9876543210 today!",
    "Astrologer Guruji solves all life and relationship problems within 24 hours in {area}. 100% guaranteed results! Call now for instant solution.",
    "Exclusive 2BHK luxury apartments starting at just 45 Lakhs in prime {area} location! Swimming pool, gym, clubhouse. Book site visit: www.dreamhomes-fake.com",
    "IPL Cricket match highlights: Thrilling last over finish as Mumbai defeats Chennai! Watch full video and match statistics here.",
    "Lose 10 kg in 15 days with herbal miracle tea! Approved by global health experts. Cash on delivery available in {area}. Order now!",
    "Celebrity spotted dining at popular cafe in {area}! You won't believe what they wore — photos inside!",
    "Congratulations! Your phone number won a cash prize of 25,00,000 INR from International Lucky Draw! Send details to claim prize instantly."
]

CODE_MIXED_TEMPLATES = [
    ("road_closure", "Road band hai {area} se {landmark} tak flyover repair ke kaaran. Please {alt_route} se detour le lijiye, bahut heavy traffic jam hai."),
    ("water_supply", "Paani ka supply kal subah 6 baje se band rahega {area} mein. GHMC pipeline repair work chal raha hai, sab log paani bhar ke rakh lo."),
    ("power_cut", "Current cut alert: {area} mein kal 10 AM to 4 PM electricity nahi aayegi. Substation maintenance work planned hai."),
    ("severe_weather", "Bhaari baarish alert! {area} mein bohot tez baarish aur toofan ka warning hai. Ghar se bahar mat niklo, ped girne ka darr hai."),
    ("public_service", "{area} ke saare schools aur colleges kal band rahenge collectors order se. Heavy rainfall declared."),
    ("road_closure", "Begumpet main road block aindi accident valla. Ameerpet vaipu vellevallu alternative route teesukondi."),
    ("water_supply", "{area} lo repu morning water supply undadu. Main water pipe burst aindi, repair chestunnaru."),
    ("power_cut", "Kukatpally area lo electricity pothundi tomorrow afternoon 2 PM to 5 PM. Transformer testing jarugutundi."),
    ("severe_weather", "Bengaluru lo heavy rains vastunnayi. {area} railway underpass lo water block aindi, avoid that route."),
    ("public_service", "Bus routes change ayyayi {area} daggara road work valla. Check new timing schedule.")
]

ROADS = [
    "Outer Ring Road", "Inner Ring Road", "NH-44 Expressway", "MG Road stretch",
    "Old Airport Road", "100 Feet Road", "Ring Road Junction", "Station Road",
    "Bannerghatta Main Road", "PVNR Elevated Expressway", "Hosur Main Road"
]

LANDMARKS = [
    "Clock Tower", "Metro Station Pillar 124", "Central Hospital Junction",
    "District Collectorate", "Flyover underpass", "Bus Terminal Complex",
    "City Sports Stadium", "Water Reservoir Gate", "Sub-station #4", "Market Complex"
]

ALT_ROUTES = [
    "Bypass Expressway", "Parallel Service Lane", "Old Canal Road", "Ring Corridor",
    "Colony Internal Roads", "East Arterial link", "Northern Link Highway"
]

TIMES = [
    ("06:00 AM", "02:00 PM"), ("08:00 AM", "12:00 PM"), ("10:00 AM", "04:00 PM"),
    ("11:00 PM", "05:00 AM"), ("01:00 PM", "06:00 PM"), ("09:00 AM", "01:00 PM"),
    ("02:00 PM", "08:00 PM")
]

DATES = ["tomorrow", "Wednesday, Oct 28", "29/10/2026", "this coming Friday", "Nov 2nd", "next Monday"]
DURATIONS = ["2 to 3 hours", "4 hours", "approx 6 hours", "until midnight"]


def inject_noise(text: str) -> str:
    """Inject realistic typos, abbreviations, and casing variations."""
    r = random.random()
    if r < 0.25:
        # Abbreviate words
        subs = {
            "Road": "Rd.", "road": "rd.", "Street": "St.", "Avenue": "Ave.",
            "Government": "Govt", "government": "govt", "Department": "Dept",
            "hospital": "hosp", "Doctor": "Dr.", "District": "Dist."
        }
        for k, v in subs.items():
            if k in text and random.random() < 0.6:
                text = text.replace(k, v, 1)
    elif r < 0.5:
        # Swap adjacent characters in a random middle word
        words = text.split()
        if len(words) > 4:
            idx = random.randint(2, len(words) - 2)
            w = words[idx]
            if len(w) > 4 and w.isalpha():
                i = random.randint(1, len(w) - 2)
                w_scrambled = w[:i] + w[i+1] + w[i] + w[i+2:]
                words[idx] = w_scrambled
                text = " ".join(words)
    elif r < 0.7:
        # Drop a vowel from a long word
        words = text.split()
        if len(words) > 4:
            idx = random.randint(1, len(words) - 2)
            w = words[idx]
            if len(w) > 5 and w.isalpha():
                vowels = [i for i, c in enumerate(w) if c.lower() in "aeiou" and i > 0]
                if vowels:
                    drop_idx = random.choice(vowels)
                    words[idx] = w[:drop_idx] + w[drop_idx+1:]
                    text = " ".join(words)
    elif r < 0.85:
        # Make a sentence ALL CAPS for urgent tone
        sentences = text.split(". ")
        if sentences:
            sentences[0] = sentences[0].upper()
            text = ". ".join(sentences)
    return text


def generate_item(
    item_id: int,
    category: str,
    template: str,
    is_spam: bool = False,
    is_code_mixed: bool = False,
    forced_severity: str = None
) -> Dict[str, Any]:
    area = random.choice(ALL_AREAS)
    road = random.choice(ROADS)
    landmark = random.choice(LANDMARKS)
    alt_route = random.choice(ALT_ROUTES)
    t1, t2 = random.choice(TIMES)
    d1 = random.choice(DATES)
    d2 = "subsequent evening"
    dur = random.choice(DURATIONS)

    text = template.format(
        area=area,
        road=road,
        landmark=landmark,
        alt_route=alt_route,
        time1=t1,
        time2=t2,
        date=d1,
        end_date=d2,
        duration=dur
    )

    if not is_spam and not is_code_mixed and random.random() < 0.12:
        text = inject_noise(text)

    # Assign realistic severity
    if is_spam:
        severity = "info"
    elif forced_severity:
        severity = forced_severity
    elif category == "severe_weather":
        severity = random.choices(["warning", "critical", "advisory"], weights=[0.45, 0.40, 0.15])[0]
    elif category in ["power_cut", "water_supply"]:
        severity = random.choices(["advisory", "warning", "info", "critical"], weights=[0.50, 0.30, 0.15, 0.05])[0]
    elif category == "road_closure":
        severity = random.choices(["warning", "advisory", "critical", "info"], weights=[0.40, 0.40, 0.10, 0.10])[0]
    elif category == "public_service":
        severity = random.choices(["info", "advisory", "warning"], weights=[0.55, 0.35, 0.10])[0]
    else:
        severity = random.choices(["info", "advisory"], weights=[0.8, 0.2])[0]

    source_pool = SOURCES["official"] if not is_spam and random.random() < 0.65 else SOURCES["news"]
    source_name = "Commercial Advertisement" if is_spam else random.choice(source_pool)
    source_type = "manual" if is_code_mixed else random.choice(["rss", "rss", "url", "manual"])

    return {
        "id": item_id,
        "text": text,
        "category": category,
        "severity": severity,
        "is_spam": is_spam,
        "affected_area": area,
        "source_name": source_name,
        "source_type": source_type,
        "is_code_mixed": is_code_mixed
    }


def main():
    items: List[Dict[str, Any]] = []
    current_id = 1

    # 1. Road Closure: 110
    for _ in range(110):
        tmpl = random.choice(ROAD_TEMPLATES)
        items.append(generate_item(current_id, "road_closure", tmpl))
        current_id += 1

    # 2. Water Supply: 100
    for _ in range(100):
        tmpl = random.choice(WATER_TEMPLATES)
        items.append(generate_item(current_id, "water_supply", tmpl))
        current_id += 1

    # 3. Power Cut: 100
    for _ in range(100):
        tmpl = random.choice(POWER_TEMPLATES)
        items.append(generate_item(current_id, "power_cut", tmpl))
        current_id += 1

    # 4. Severe Weather: 100
    for _ in range(100):
        tmpl = random.choice(WEATHER_TEMPLATES)
        items.append(generate_item(current_id, "severe_weather", tmpl))
        current_id += 1

    # 5. Public Service: 100
    for _ in range(100):
        tmpl = random.choice(PUBLIC_SERVICE_TEMPLATES)
        items.append(generate_item(current_id, "public_service", tmpl))
        current_id += 1

    # 6. Other: 70
    for _ in range(70):
        tmpl = random.choice(OTHER_TEMPLATES)
        items.append(generate_item(current_id, "other", tmpl))
        current_id += 1

    # 7. Spam: 70
    for _ in range(70):
        tmpl = random.choice(SPAM_TEMPLATES)
        items.append(generate_item(current_id, "other", tmpl, is_spam=True, forced_severity="info"))
        current_id += 1

    # 8. Code-mixed (Telugu / Hindi transliterated): 15
    for cat, tmpl in CODE_MIXED_TEMPLATES:
        items.append(generate_item(current_id, cat, tmpl, is_spam=False, is_code_mixed=True))
        current_id += 1

    while len([it for it in items if it.get("is_code_mixed")]) < 15:
        cat, tmpl = random.choice(CODE_MIXED_TEMPLATES)
        items.append(generate_item(current_id, cat, tmpl, is_spam=False, is_code_mixed=True))
        current_id += 1

    total = len(items)
    print(f"Total reports generated: {total}")

    # Shuffle with fixed seed
    random.shuffle(items)

    # Re-assign sequential IDs
    for idx, it in enumerate(items, 1):
        it["id"] = idx

    # Category counts
    cat_counts = {}
    sev_counts = {}
    spam_count = 0
    code_mixed_count = 0
    for it in items:
        c = it["category"]
        s = it["severity"]
        cat_counts[c] = cat_counts.get(c, 0) + 1
        sev_counts[s] = sev_counts.get(s, 0) + 1
        if it["is_spam"]:
            spam_count += 1
        if it["is_code_mixed"]:
            code_mixed_count += 1

    print("\n--- Category Breakdown ---")
    for c, cnt in sorted(cat_counts.items()):
        print(f"  {c:15s}: {cnt}")
    print(f"  {'[spam]':15s}: {spam_count}")
    print(f"  {'[code_mixed]':15s}: {code_mixed_count}")

    print("\n--- Severity Breakdown ---")
    for s, cnt in sorted(sev_counts.items()):
        print(f"  {s:15s}: {cnt}")

    # Save master dataset
    master_path = OUTPUT_DIR / "seed_data.json"
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"\nSaved master dataset to {master_path}")

    # Splits (70% train, 15% val, 15% test)
    n_train = int(total * 0.70)
    n_val = int(total * 0.15)
    train_items = items[:n_train]
    val_items = items[n_train:n_train + n_val]
    test_items = items[n_train + n_val:]

    print(f"\nSplit Sizes: Train={len(train_items)}, Val={len(val_items)}, Test={len(test_items)}")

    with open(OUTPUT_DIR / "train.json", "w", encoding="utf-8") as f:
        json.dump(train_items, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_DIR / "val.json", "w", encoding="utf-8") as f:
        json.dump(val_items, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_DIR / "test.json", "w", encoding="utf-8") as f:
        json.dump(test_items, f, indent=2, ensure_ascii=False)
    print("Saved train.json, val.json, and test.json successfully.")


if __name__ == "__main__":
    main()
