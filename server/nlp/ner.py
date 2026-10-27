"""Named Entity Recognition (NER) module for CivicPulse.

Extracts geographic locations, facilities, and municipal entities using spaCy
as a classical baseline before LLM structured synthesis.
"""

import logging
from typing import Any, Dict, List

import spacy

logger = logging.getLogger(__name__)

# Load en_core_web_sm
try:
    nlp_ner = spacy.load("en_core_web_sm")
except Exception as e:
    logger.warning(f"Failed to load spaCy NER model: {e}")
    nlp_ner = None

TARGET_LABELS = {"GPE", "LOC", "FAC", "ORG"}


def extract_entities_spacy(text: str) -> Dict[str, List[str]]:
    """Extract geographical entities (GPE, LOC, FAC) and organizations (ORG) using spaCy."""
    if nlp_ner is None or not text:
        return {"locations": [], "facilities": [], "organizations": []}

    doc = nlp_ner(text)

    locations = set()
    facilities = set()
    organizations = set()

    for ent in doc.ents:
        cleaned = ent.text.strip()
        if len(cleaned) < 3:
            continue
        if ent.label_ in {"GPE", "LOC"}:
            locations.add(cleaned)
        elif ent.label_ == "FAC":
            facilities.add(cleaned)
        elif ent.label_ == "ORG":
            organizations.add(cleaned)

    return {
        "locations": sorted(list(locations)),
        "facilities": sorted(list(facilities)),
        "organizations": sorted(list(organizations))
    }


def compare_ner_with_llm(
    spacy_entities: List[str],
    llm_entities: List[str]
) -> Dict[str, Any]:
    """Compare spaCy classical NER entity extraction with LLM extracted areas."""
    s_set = {s.lower() for s in spacy_entities}
    l_set = {l.lower() for l in llm_entities}

    overlap = s_set.intersection(l_set)
    spacy_only = s_set - l_set
    llm_only = l_set - s_set

    jaccard = len(overlap) / len(s_set.union(l_set)) if (s_set or l_set) else 1.0

    return {
        "overlap_count": len(overlap),
        "spacy_count": len(s_set),
        "llm_count": len(l_set),
        "jaccard_similarity": round(jaccard, 3),
        "common_entities": list(overlap),
        "spacy_unique": list(spacy_only),
        "llm_unique": list(llm_only)
    }
