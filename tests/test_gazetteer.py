"""Tests for Hyderabad Locality Gazetteer and Spatial Radius Matching."""

import pytest
from server.nlp.gazetteer import (
    HYDERABAD_GAZETTEER,
    haversine_distance,
    resolve_locality,
    extract_localities_from_text,
    is_alert_within_radius,
)


def test_gazetteer_loaded():
    """Verify Hyderabad gazetteer contains key localities."""
    assert len(HYDERABAD_GAZETTEER) >= 30
    assert "Gachibowli" in HYDERABAD_GAZETTEER
    assert "Madhapur" in HYDERABAD_GAZETTEER
    assert "Kukatpally" in HYDERABAD_GAZETTEER
    assert "Banjara Hills" in HYDERABAD_GAZETTEER


def test_exact_and_alias_resolution():
    """Test alias and cross road resolution to canonical names."""
    # "Gachibowli X Roads" -> Gachibowli
    g1 = resolve_locality("Gachibowli X Roads")
    assert g1 is not None
    assert g1["canonical_name"] == "Gachibowli"
    assert g1["match_confidence"] >= 0.9

    # "Gachibowli Road" -> Gachibowli
    g2 = resolve_locality("Gachibowli Road")
    assert g2 is not None
    assert g2["canonical_name"] == "Gachibowli"

    # "Cyber Towers" -> Hitec City
    h1 = resolve_locality("Cyber Towers")
    assert h1 is not None
    assert h1["canonical_name"] == "Hitec City"

    # "kphb 9th phase" -> Kukatpally
    k1 = resolve_locality("kphb 9th phase")
    assert k1 is not None
    assert k1["canonical_name"] == "Kukatpally"


def test_fuzzy_matching_misspelling():
    """Test fuzzy matching on misspelled locality names."""
    res = resolve_locality("Gatchibowli")
    assert res is not None
    assert res["canonical_name"] == "Gachibowli"

    res2 = resolve_locality("Madapur")
    assert res2 is not None
    assert res2["canonical_name"] == "Madhapur"


def test_haversine_distance():
    """Test Haversine distance calculations between known Hyderabad points."""
    # Distance between Gachibowli (17.4401, 78.3489) and Hitec City (17.4435, 78.3772) is approx 3 km
    dist = haversine_distance(17.4401, 78.3489, 17.4435, 78.3772)
    assert 2.0 <= dist <= 4.0

    # Distance to self is 0
    assert haversine_distance(17.4401, 78.3489, 17.4401, 78.3489) == 0.0


def test_extract_localities_from_text():
    """Test extracting multiple localities mentioned in natural municipal notice."""
    text = "Traffic advisory: Waterlogging reported near Gachibowli X Roads and Cyber Towers junction in Hitec City. Commuters to Madhapur advised detour."
    extracted = extract_localities_from_text(text)
    names = [e["canonical_name"] for e in extracted]
    assert "Gachibowli" in names
    assert "Hitec City" in names
    assert "Madhapur" in names


def test_is_alert_within_radius():
    """Test radius boundary checks for alerts."""
    alert_areas = [
        {"name": "Gachibowli", "lat": 17.4401, "lng": 78.3489}
    ]

    # User at Hitec City (~3 km away) with 5 km radius should match
    in_range, dist = is_alert_within_radius(alert_areas, 17.4435, 78.3772, 5.0)
    assert in_range is True
    assert dist <= 5.0

    # User at Charminar (~16 km away) with 5 km radius should NOT match
    in_range, dist = is_alert_within_radius(alert_areas, 17.3616, 78.4747, 5.0)
    assert in_range is False
    assert dist > 10.0
