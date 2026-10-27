"""Gemini LLM Extraction Service for CivicPulse.

Extracts structured alert fields (title, category, severity, coordinates,
impact, and recommended citizen actions) using Gemini 1.5 / 2.0 with prompt templates.
Includes a fully offline fallback parser when API keys or network are unavailable.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from server.config import settings
from server.nlp.ner import extract_entities_spacy
from server.nlp.gazetteer import extract_localities_from_text, resolve_locality
from server.nlp.time_extractor import extract_temporal_fields
from server.schemas.alert import AlertBase

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "extract_alert.txt"

# Known coordinates lookup for major urban localities
AREA_COORDINATES = {
    "begumpet": (17.4447, 78.4664),
    "ameerpet": (17.4375, 78.4482),
    "hitec city": (17.4435, 78.3772),
    "madhapur": (17.4483, 78.3915),
    "gachibowli": (17.4401, 78.3489),
    "kukatpally": (17.4947, 78.3996),
    "banjara hills": (17.4156, 78.4350),
    "jubilee hills": (17.4319, 78.4073),
    "secunderabad": (17.4399, 78.4983),
    "indiranagar": (12.9784, 77.6408),
    "koramangala": (12.9352, 77.6245),
    "whitefield": (12.9698, 77.7500),
    "hsr layout": (12.9121, 77.6446),
    "electronic city": (12.8452, 77.6602),
    "t. nagar": (13.0418, 80.2341),
    "adyar": (13.0012, 80.2565),
    "velachery": (12.9815, 80.2180),
    "connaught place": (28.6315, 77.2167),
    "lajpat nagar": (28.5700, 77.2400),
    "rohini": (28.7495, 77.0565),
}


class GeminiExtractionService:
    """Extracts validated structured alert schemas from unstructured reports."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client_ready = False

        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                self.client_ready = True
                logger.info("Gemini Extraction Service initialized with API key.")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini: {e}")

    def extract_structured_alert(
        self,
        raw_text: str,
        predicted_category: Optional[str] = None,
        predicted_severity: Optional[str] = None,
        source_name: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured alert using Gemini if configured, else offline heuristic fallback."""
        if self.client_ready:
            try:
                return self._extract_via_gemini(raw_text, source_name, source_url)
            except Exception as e:
                logger.error(f"Gemini API call failed, falling back to offline extractor: {e}")

        return self._extract_offline_fallback(
            raw_text, predicted_category, predicted_severity, source_name, source_url
        )

    def _extract_via_gemini(
        self,
        raw_text: str,
        source_name: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call Gemini LLM with prompt template."""
        if not PROMPT_FILE.exists():
            raise FileNotFoundError(f"Prompt template missing at {PROMPT_FILE}")

        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            template = f.read()

        prompt = template.replace("{report_text}", raw_text)
        response = self.model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        clean_json_str = response.text.strip()
        if clean_json_str.startswith("```json"):
            clean_json_str = clean_json_str[7:-3].strip()

        data = json.loads(clean_json_str)

        # Merge known source if not populated by LLM
        if source_name and not data.get("source_name"):
            data["source_name"] = source_name
        if source_url and not data.get("source_url"):
            data["source_url"] = source_url

        # Validate with Pydantic
        AlertBase(**data)
        return data

    def _extract_offline_fallback(
        self,
        raw_text: str,
        predicted_category: Optional[str] = None,
        predicted_severity: Optional[str] = None,
        source_name: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Deterministic NLP-based structured extraction for full offline functionality."""
        # Extract localities via Hyderabad Gazetteer with alias & fuzzy resolution
        gazetteer_locs = extract_localities_from_text(raw_text)
        affected_areas = []
        seen_names = set()

        for g_loc in gazetteer_locs:
            c_name = g_loc["canonical_name"]
            if c_name not in seen_names:
                seen_names.add(c_name)
                affected_areas.append({
                    "name": c_name,
                    "lat": g_loc["lat"],
                    "lng": g_loc["lng"]
                })

        # If no gazetteer matches found directly, check spaCy NER entities against gazetteer
        if not affected_areas:
            ner_res = extract_entities_spacy(raw_text)
            for loc in ner_res["locations"] + ner_res["facilities"]:
                resolved = resolve_locality(loc)
                if resolved and resolved["canonical_name"] not in seen_names:
                    seen_names.add(resolved["canonical_name"])
                    affected_areas.append({
                        "name": resolved["canonical_name"],
                        "lat": resolved["lat"],
                        "lng": resolved["lng"]
                    })
                elif loc not in seen_names:
                    seen_names.add(loc)
                    coords = AREA_COORDINATES.get(loc.lower(), (17.3850, 78.4867))
                    affected_areas.append({
                        "name": loc,
                        "lat": coords[0],
                        "lng": coords[1]
                    })

        if not affected_areas:
            affected_areas.append({"name": "Hyderabad Metropolitan Area", "lat": 17.3850, "lng": 78.4867})

        cat = predicted_category or "other"
        sev = predicted_severity or "info"
        loc = affected_areas[0]["name"] if affected_areas else "Hyderabad"

        # Construct clean headline from first sentence without mid-word cutting
        cleaned_text = re.sub(r"\s+", " ", raw_text).strip()
        sentences = re.split(r"(?<=[.!?])\s+", cleaned_text)
        if sentences and sentences[0]:
            first_sent = sentences[0].strip().rstrip(".")
            if len(first_sent) > 140:
                title = first_sent[:140].rsplit(" ", 1)[0] + "…"
            else:
                title = first_sent
        else:
            title = "Civic Notification"

        # Action templates based on category (3 to 4 concrete actionable checklist items)
        actions_map = {
            "road_closure": [
                "Plan an alternate detour route avoiding the impacted junction.",
                "Expect 20–30 minutes additional commute delay during peak rush hours.",
                "Follow directional signage and Hyderabad Traffic Police marshals' instructions.",
                "Use Hyderabad Metro or public transit to bypass arterial road congestion."
            ],
            "water_supply": [
                "Store at least 20–30 liters of drinking and household water in advance.",
                "Boil municipal water for at least 3 minutes before consumption if pressure drops.",
                "Call HMWSSB helpline (1916) or use mobile app to book priority water tankers.",
                "Turn off booster pumps to prevent motor burnout during zero-pressure hours."
            ],
            "power_cut": [
                "Keep essential medical life-support devices, UPS inverters, and phones fully charged.",
                "Unplug sensitive electronics and air conditioners to avoid voltage surge damage.",
                "Keep deep freezers and refrigerators closed to preserve food freshness.",
                "Report localized feeder trips or wire hazards to TGSPDCL hotline (1912)."
            ],
            "severe_weather": [
                "Stay indoors and avoid parking vehicles beneath old trees or overhead cables.",
                "Do not drive through inundated underpasses or submerged low-lying road stretches.",
                "Keep emergency flashlights, battery radios, and first aid kits accessible.",
                "Monitor GHMC Disaster Response Force (DRF) real-time alerts on 040-21111111."
            ],
            "public_service": [
                "Verify official counter operating hours and required documents before visiting.",
                "Use online municipal portals (ghmc.gov.in) for non-urgent citizen grievances.",
                "Follow on-site queue tokens and administrative guidance.",
                "Contact the municipal citizen helpline (040-21111111) for service assistance."
            ],
            "public_health": [
                "Verify dispensary/health camp operating hours and bring valid government ID.",
                "Ensure routine prescriptions and emergency medicines are replenished in advance.",
                "Follow sanitation protocols and vector control advisories in your neighborhood.",
                "Contact Telangana Health Helpline (104) for medical guidance."
            ],
            "other": [
                "Follow municipal advisories.",
                "Plan alternate arrangements."
            ]
        }

        impact_map = {
            "road_closure": f"Traffic movement restricted around {loc} due to municipal works or event. Diversions in effect.",
            "water_supply": f"Drinking water supply suspended or low pressure across {loc}. Tanker supplies deployed for critical needs.",
            "power_cut": f"Scheduled electricity shutdown impacting residential and commercial feeders in {loc}.",
            "severe_weather": f"Extreme weather conditions forecast in {loc}. Risk of waterlogging, strong wind gusts, and fallen branches.",
            "public_service": f"Temporary modification in public utility service operations in {loc}. Administrative counters updated.",
            "public_health": f"Public health camp or municipal medical initiative active in {loc}. Health services operating on adjusted schedules.",
            "other": f"Civic bulletin issued for {loc} residents."
        }

        # Extract structured temporal timing fields
        temporal = extract_temporal_fields(raw_text)

        return {
            "title": title,
            "category": cat,
            "severity": sev,
            "affected_areas": affected_areas,
            "start_time": temporal["start_time"],
            "expected_end_time": temporal["expected_end_time"],
            "expected_impact": impact_map.get(cat, "Public advisory in effect."),
            "recommended_actions": actions_map.get(cat, ["Follow local civil guidance."]),
            "source_name": source_name or "Municipal Public Bulletin",
            "source_url": source_url,
            "published_at": None,
            "confidence": 0.88,
            "needs_review": False
        }


gemini_service = GeminiExtractionService()
