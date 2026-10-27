"""Hyderabad Locality Gazetteer and Hyperlocal Spatial Matching for CivicPulse.

Provides:
1. Canonical locality directory with GPS coordinates, aliases, spelling variants, and zones.
2. Fast alias lookup and fuzzy string matching (resolves e.g. "Gachibowli X Roads" -> "Gachibowli").
3. Great-circle Haversine distance calculations for radius-based alert matching.
4. Spatial locality extraction from unformatted municipal announcements.
"""

import math
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

# Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0

# Comprehensive Hyderabad Locality Directory
# Lat/Lng centered on major transit nodes, flyovers, and municipal ward centers.
HYDERABAD_GAZETTEER: Dict[str, Dict[str, Any]] = {
    "Gachibowli": {
        "canonical_name": "Gachibowli",
        "lat": 17.4401,
        "lng": 78.3489,
        "radius_km": 3.5,
        "zone": "West Zone (Serilingampally)",
        "aliases": [
            "gachibowli", "gachibowli x roads", "gachibowli road", "gachibowli cross roads",
            "gachibowli flyover", "gachibowli junction", "gatchibowli", "gachiboli",
            "gachibowli circle", "gachibowli stadium", "gachibowli orr"
        ]
    },
    "Madhapur": {
        "canonical_name": "Madhapur",
        "lat": 17.4483,
        "lng": 78.3915,
        "radius_km": 3.0,
        "zone": "West Zone (Serilingampally)",
        "aliases": [
            "madhapur", "madhapur main road", "madhapur metro", "inorbit mall",
            "durgam cheruvu", "madapur", "ayyappa society", "kavuri hills",
            "silpa gramam", "shilparamam"
        ]
    },
    "Hitec City": {
        "canonical_name": "Hitec City",
        "lat": 17.4435,
        "lng": 78.3772,
        "radius_km": 3.0,
        "zone": "West Zone (Serilingampally)",
        "aliases": [
            "hitec city", "cyber towers", "cyber city", "hitech city", "cyberabad",
            "mindspace", "hi-tech city", "raheja mindspace", "knowledge city",
            "t-hub", "cyber gateway"
        ]
    },
    "Kondapur": {
        "canonical_name": "Kondapur",
        "lat": 17.4699,
        "lng": 78.3578,
        "radius_km": 3.0,
        "zone": "West Zone (Serilingampally)",
        "aliases": [
            "kondapur", "kondapur rto", "kothaguda", "kothaguda junction",
            "kothaguda x roads", "kondapur x roads", "botanical garden road",
            "botanical gardens", "harsha hospital kondapur"
        ]
    },
    "Kukatpally": {
        "canonical_name": "Kukatpally",
        "lat": 17.4947,
        "lng": 78.3996,
        "radius_km": 4.0,
        "zone": "North Zone (Kukatpally)",
        "aliases": [
            "kukatpally", "kphb", "kphb colony", "kukatpally housing board",
            "jntu", "jntu hyderabad", "kukatpally y junction", "kphb 9th phase",
            "kphb phase", "kukatpally metro"
        ]
    },
    "Banjara Hills": {
        "canonical_name": "Banjara Hills",
        "lat": 17.4156,
        "lng": 78.4350,
        "radius_km": 3.5,
        "zone": "Central Zone (Khairatabad)",
        "aliases": [
            "banjara hills", "road no 1 banjara hills", "road no 12 banjara hills",
            "road no 10 banjara hills", "taj krishna", "star hospital banjara",
            "care hospital banjara", "basavatarakam cancer hospital"
        ]
    },
    "Jubilee Hills": {
        "canonical_name": "Jubilee Hills",
        "lat": 17.4319,
        "lng": 78.4073,
        "radius_km": 3.5,
        "zone": "Central Zone (Khairatabad)",
        "aliases": [
            "jubilee hills", "jubilee hills check post", "road no 36 jubilee hills",
            "road no 45 jubilee hills", "road no 10 jubilee hills", "peddamma temple",
            "apollo hospital jubilee hills", "filmnagar", "film nagar"
        ]
    },
    "Begumpet": {
        "canonical_name": "Begumpet",
        "lat": 17.4447,
        "lng": 78.4664,
        "radius_km": 3.0,
        "zone": "North Zone (Secunderabad)",
        "aliases": [
            "begumpet", "begumpet airport", "begumpet flyover", "prakash nagar",
            "rasoolpura", "begumpet railway station", "varun motors begumpet"
        ]
    },
    "Ameerpet": {
        "canonical_name": "Ameerpet",
        "lat": 17.4375,
        "lng": 78.4482,
        "radius_km": 2.5,
        "zone": "Central Zone (Khairatabad)",
        "aliases": [
            "ameerpet", "ameerpet x roads", "ameerpet cross roads", "ameerpet metro",
            "sarathi studios", "satyam theatre", "dharam karam road", "sr nagar",
            "sanjeeva reddy nagar", "balkampet"
        ]
    },
    "Secunderabad": {
        "canonical_name": "Secunderabad",
        "lat": 17.4399,
        "lng": 78.4983,
        "radius_km": 4.5,
        "zone": "North Zone (Secunderabad)",
        "aliases": [
            "secunderabad", "secunderabad railway station", "paradise circle",
            "clock tower", "patny", "patny circle", "marredpally",
            "west marredpally", "east marredpally", "karkhana", "mg road secunderabad"
        ]
    },
    "Miyapur": {
        "canonical_name": "Miyapur",
        "lat": 17.4968,
        "lng": 78.3614,
        "radius_km": 3.5,
        "zone": "North Zone (Serilingampally)",
        "aliases": [
            "miyapur", "miyapur x roads", "miyapur cross roads", "miyapur metro",
            "allwyn x roads", "allwyn colony", "hafeezpet", "hafeezpet flyover"
        ]
    },
    "Dilsukhnagar": {
        "canonical_name": "Dilsukhnagar",
        "lat": 17.3688,
        "lng": 78.5247,
        "radius_km": 3.0,
        "zone": "East Zone (L.B. Nagar)",
        "aliases": [
            "dilsukhnagar", "dilsukhnagar bus stand", "dilsukhnagar metro",
            "chaitanyapuri", "malakpet", "moosarambagh", "kothapet", "gaddiannaram"
        ]
    },
    "LB Nagar": {
        "canonical_name": "LB Nagar",
        "lat": 17.3457,
        "lng": 78.5522,
        "radius_km": 4.0,
        "zone": "East Zone (L.B. Nagar)",
        "aliases": [
            "lb nagar", "l.b. nagar", "lb nagar ring road", "kamineni hospital",
            "sagar ring road", "bairamalguda", "mansoorabad", "nagole", "nagole x roads"
        ]
    },
    "Uppal": {
        "canonical_name": "Uppal",
        "lat": 17.4018,
        "lng": 78.5602,
        "radius_km": 3.5,
        "zone": "East Zone (Uppal)",
        "aliases": [
            "uppal", "uppal ring road", "uppal x roads", "uppal stadium",
            "rajiv gandhi stadium", "ramanthapur", "habsiguda", "tarnaka uppal road",
            "uppal metro", "peerzadiguda", "boduppal"
        ]
    },
    "Mehdipatnam": {
        "canonical_name": "Mehdipatnam",
        "lat": 17.3916,
        "lng": 78.4420,
        "radius_km": 3.0,
        "zone": "South-West Zone (Charminar)",
        "aliases": [
            "mehdipatnam", "mehdipatnam rythu bazaar", "pvnr expressway",
            "pv narasimha rao expressway", "sarojini devi eye hospital",
            "rethink junction", "pillar 1 pvnr", "pillar 20 pvnr"
        ]
    },
    "Charminar": {
        "canonical_name": "Charminar",
        "lat": 17.3616,
        "lng": 78.4747,
        "radius_km": 3.0,
        "zone": "South Zone (Old City)",
        "aliases": [
            "charminar", "old city", "laad bazaar", "makkah masjid", "madina",
            "nayapul", "afzalgunj", "salargunj", "mozzamjahi market", "high court hyderabad",
            "pathargatti", "gulzar houz"
        ]
    },
    "Nanakramguda": {
        "canonical_name": "Nanakramguda",
        "lat": 17.4150,
        "lng": 78.3423,
        "radius_km": 3.0,
        "zone": "West Zone (Financial District)",
        "aliases": [
            "nanakramguda", "financial district", "waverock", "wipro circle",
            "q-city", "gachibowli financial district", "us consulate hyderabad",
            "kokapet", "kokapet seaz", "gar infobahn"
        ]
    },
    "Manikonda": {
        "canonical_name": "Manikonda",
        "lat": 17.4009,
        "lng": 78.3798,
        "radius_km": 3.0,
        "zone": "West Zone (Rajendranagar)",
        "aliases": [
            "manikonda", "puppalguda", "ou colony manikonda", "shaikpet",
            "shaikpet flyover", "whisper valley", "al-saba", "lanco hills"
        ]
    },
    "Tolichowki": {
        "canonical_name": "Tolichowki",
        "lat": 17.3984,
        "lng": 78.4140,
        "radius_km": 2.5,
        "zone": "South-West Zone (Khairatabad)",
        "aliases": [
            "tolichowki", "tolichowki flyover", "paramount colony", "seven tombs",
            "qutb shahi tombs", "golconda", "golconda fort", "nanal nagar"
        ]
    },
    "Khairatabad": {
        "canonical_name": "Khairatabad",
        "lat": 17.4123,
        "lng": 78.4583,
        "radius_km": 2.5,
        "zone": "Central Zone (Khairatabad)",
        "aliases": [
            "khairatabad", "khairatabad flyover", "khairatabad rto", "necklace road",
            "hussain sagar", "tank bund", "imsa building", "shadan college"
        ]
    },
    "Panjagutta": {
        "canonical_name": "Panjagutta",
        "lat": 17.4265,
        "lng": 78.4485,
        "radius_km": 2.5,
        "zone": "Central Zone (Khairatabad)",
        "aliases": [
            "panjagutta", "punjagutta", "nagarjuna circle", "punjagutta x roads",
            "panjagutta flyover", "somajiguda", "raj bhavan road", "nims hospital"
        ]
    },
    "Tarnaka": {
        "canonical_name": "Tarnaka",
        "lat": 17.4284,
        "lng": 78.5318,
        "radius_km": 2.5,
        "zone": "East Zone (Secunderabad)",
        "aliases": [
            "tarnaka", "tarnaka flyover", "osmania university", "ou campus",
            "ngri", "iict", "habsiguda", "lalaguda"
        ]
    },
    "Alwal": {
        "canonical_name": "Alwal",
        "lat": 17.5028,
        "lng": 78.5065,
        "radius_km": 3.5,
        "zone": "North Zone (Malkajgiri)",
        "aliases": [
            "alwal", "old alwal", "alwal hills", "lothkunta", "bolarum",
            "trimulgherry", "machabollaram"
        ]
    },
    "Kompally": {
        "canonical_name": "Kompally",
        "lat": 17.5376,
        "lng": 78.4842,
        "radius_km": 4.0,
        "zone": "North Zone (Medchal)",
        "aliases": [
            "kompally", "kompally x roads", "jeedimetla", "suchitra",
            "suchitra circle", "medchal highway", "dulapally"
        ]
    },
    "Malkajgiri": {
        "canonical_name": "Malkajgiri",
        "lat": 17.4523,
        "lng": 78.5312,
        "radius_km": 3.0,
        "zone": "North-East Zone (Malkajgiri)",
        "aliases": [
            "malkajgiri", "safilguda", "safilguda lake", "anandbagh",
            "naredmet", "naredmet x roads", "vinayak nagar"
        ]
    },
    "ECIL": {
        "canonical_name": "ECIL",
        "lat": 17.4695,
        "lng": 78.5684,
        "radius_km": 3.5,
        "zone": "North-East Zone (Kapra)",
        "aliases": [
            "ecil", "ecil x roads", "as rao nagar", "a.s. rao nagar",
            "sainikpuri", "kamala nagar", "moula ali", "moula ali kaman", "kapra"
        ]
    },
    "Chandanagar": {
        "canonical_name": "Chandanagar",
        "lat": 17.4912,
        "lng": 78.3248,
        "radius_km": 3.5,
        "zone": "West Zone (Serilingampally)",
        "aliases": [
            "chandanagar", "lingampally", "serilingampally", "bhel",
            "ramachandrapuram", "patancheru", "beeramguda", "tellapur"
        ]
    },
    "Nizampet": {
        "canonical_name": "Nizampet",
        "lat": 17.5186,
        "lng": 78.3845,
        "radius_km": 3.5,
        "zone": "North Zone (Kukatpally)",
        "aliases": [
            "nizampet", "nizampet x roads", "nizampet village", "bachupally",
            "bachupally x roads", "pragathi nagar", "mallampet"
        ]
    },
    "Abids": {
        "canonical_name": "Abids",
        "lat": 17.3917,
        "lng": 78.4752,
        "radius_km": 2.0,
        "zone": "Central Zone (Charminar)",
        "aliases": [
            "abids", "koti", "nampally", "nampally station", "gunfoundry",
            "sultan bazar", "mozzamjahi market", "bashirbagh", "basheerbagh"
        ]
    },
    "Lakdikapul": {
        "canonical_name": "Lakdikapul",
        "lat": 17.4045,
        "lng": 78.4631,
        "radius_km": 2.0,
        "zone": "Central Zone (Khairatabad)",
        "aliases": [
            "lakdikapul", "masab tank", "saifabad", "assembly",
            "ravindra bharathi", "niloufer hospital", "red hills"
        ]
    },
    "Attapur": {
        "canonical_name": "Attapur",
        "lat": 17.3719,
        "lng": 78.4320,
        "radius_km": 3.0,
        "zone": "South-West Zone (Rajendranagar)",
        "aliases": [
            "attapur", "pillar 140", "pillar 120 pvnr", "hyderguda attapur",
            "upperpally", "rajendranagar", "aramgarh", "aramgarh x roads"
        ]
    },
    "Shamshabad": {
        "canonical_name": "Shamshabad",
        "lat": 17.2403,
        "lng": 78.4294,
        "radius_km": 6.0,
        "zone": "South Zone (Airport Corridor)",
        "aliases": [
            "shamshabad", "rgia", "hyderabad airport", "rajiv gandhi international airport",
            "gmr aero", "shamshabad junction", "orr exit 16"
        ]
    }
}


# Precomputed normalized alias lookup mapping: alias_string -> canonical_name
ALIAS_LOOKUP: Dict[str, str] = {}
for canonical, meta in HYDERABAD_GAZETTEER.items():
    ALIAS_LOOKUP[canonical.lower()] = canonical
    for alias in meta["aliases"]:
        ALIAS_LOOKUP[alias.lower()] = canonical


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Great Circle distance between two points on the Earth in kilometers."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 2)


def normalize_locality_query(text: str) -> str:
    """Clean and standardize input string for locality matching."""
    text = text.lower()
    # Remove common punctuation
    text = re.sub(r"[^\w\s-]", " ", text)
    # Standardize cross road variations
    text = re.sub(r"\bx[\s-]*roads?\b", "x roads", text)
    text = re.sub(r"\bcross[\s-]*roads?\b", "cross roads", text)
    return " ".join(text.split())


def resolve_locality(query_text: str, fuzzy_threshold: float = 0.78) -> Optional[Dict[str, Any]]:
    """Resolve an arbitrary locality query, alias, or road name to a canonical Hyderabad record.

    Example resolutions:
    - "Gachibowli X Roads" -> "Gachibowli"
    - "Gachibowli Road" -> "Gachibowli"
    - "near Inorbit Mall Madhapur" -> "Madhapur"
    - "kphb 9th phase" -> "Kukatpally"
    - "Gatchibowli" -> "Gachibowli"
    """
    if not query_text or not query_text.strip():
        return None

    cleaned = normalize_locality_query(query_text)

    # 1. Exact alias match
    if cleaned in ALIAS_LOOKUP:
        canonical = ALIAS_LOOKUP[cleaned]
        item = HYDERABAD_GAZETTEER[canonical].copy()
        item["match_confidence"] = 1.0
        item["matched_alias"] = cleaned
        return item

    # 2. Check direct substring containment (alias inside query or query inside alias)
    # Sort aliases by length descending so longer/more specific match first
    sorted_aliases = sorted(ALIAS_LOOKUP.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        # Check token boundary containment
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, cleaned):
            canonical = ALIAS_LOOKUP[alias]
            item = HYDERABAD_GAZETTEER[canonical].copy()
            item["match_confidence"] = 0.95
            item["matched_alias"] = alias
            return item

    # 3. Fuzzy match against all known aliases using SequenceMatcher
    best_ratio = 0.0
    best_canonical = None
    best_alias = None

    for alias, canonical in ALIAS_LOOKUP.items():
        ratio = SequenceMatcher(None, cleaned, alias).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_canonical = canonical
            best_alias = alias

    if best_ratio >= fuzzy_threshold and best_canonical:
        item = HYDERABAD_GAZETTEER[best_canonical].copy()
        item["match_confidence"] = round(best_ratio, 3)
        item["matched_alias"] = best_alias
        return item

    return None


def extract_localities_from_text(text: str) -> List[Dict[str, Any]]:
    """Scan natural language text and extract all referenced Hyderabad localities.

    Returns deduplicated canonical locality objects with coordinates and default radii.
    """
    if not text:
        return []

    cleaned_text = normalize_locality_query(text)
    matched_canonicals = set()
    results = []

    # Sort aliases by length descending to match longest phrases first (e.g. "Gachibowli X Roads")
    sorted_aliases = sorted(ALIAS_LOOKUP.keys(), key=len, reverse=True)

    for alias in sorted_aliases:
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, cleaned_text):
            canonical = ALIAS_LOOKUP[alias]
            if canonical not in matched_canonicals:
                matched_canonicals.add(canonical)
                item = HYDERABAD_GAZETTEER[canonical].copy()
                item["matched_alias"] = alias
                results.append(item)

    return results


def is_alert_within_radius(
    alert_areas: List[Dict[str, Any]],
    user_lat: float,
    user_lng: float,
    radius_km: float
) -> Tuple[bool, float]:
    """Check if any affected area in an alert falls within radius_km of the user coordinate.

    Returns:
        (is_within_radius, minimum_distance_km)
    """
    if not alert_areas:
        return False, float("inf")

    min_dist = float("inf")
    for area in alert_areas:
        if not isinstance(area, dict):
            continue
        alat = area.get("lat")
        alng = area.get("lng")
        if alat is not None and alng is not None:
            dist = haversine_distance(user_lat, user_lng, float(alat), float(alng))
            if dist < min_dist:
                min_dist = dist

    return min_dist <= radius_km, min_dist
