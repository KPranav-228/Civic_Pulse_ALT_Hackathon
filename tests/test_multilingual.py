"""Tests for Phase 6: Multilingual Alert Generation (English, Telugu, Hindi)."""

import pytest
from server.services.multilingual import (
    translate_alert_offline,
    translate_alert,
    CATEGORY_TRANSLATIONS,
    SEVERITY_TRANSLATIONS,
)


def test_category_and_severity_translations():
    """Verify dictionary translation mappings for Telugu and Hindi."""
    assert CATEGORY_TRANSLATIONS["water_supply"]["te"] == "మంచినీటి సరఫరా అంతరాయం"
    assert CATEGORY_TRANSLATIONS["water_supply"]["hi"] == "जलापूर्ति में रुकावट"
    assert CATEGORY_TRANSLATIONS["power_cut"]["te"] == "విద్యుత్ సరఫరా కోత"
    assert CATEGORY_TRANSLATIONS["power_cut"]["hi"] == "बिजली कटौती"

    assert SEVERITY_TRANSLATIONS["critical"]["te"] == "అత్యవసరం"
    assert SEVERITY_TRANSLATIONS["critical"]["hi"] == "अति गंभीर"


def test_translate_alert_offline_telugu():
    """Verify complete alert translation into Telugu."""
    res = translate_alert_offline(
        title="Pipeline rupture in Madhapur",
        category="water_supply",
        severity="critical",
        impact="Water shutdown for 24 hours.",
        actions=["Store sufficient drinking water in advance."],
        target_lang="te"
    )

    assert res["language"] == "te"
    assert "మంచినీటి సరఫరా అంతరాయం" in res["title"]
    assert "అత్యవసరం" == res["severity_label"]
    assert len(res["recommended_actions"]) > 0
    # Verify Telugu script characters present
    assert any("\u0c00" <= ch <= "\u0c7f" for ch in res["recommended_actions"][0])


def test_translate_alert_offline_hindi():
    """Verify complete alert translation into Hindi."""
    res = translate_alert_offline(
        title="Severe power cut in Gachibowli",
        category="power_cut",
        severity="warning",
        impact="Power outage from 10 AM to 4 PM.",
        actions=["Keep essential devices charged."],
        target_lang="hi"
    )

    assert res["language"] == "hi"
    assert "बिजली कटौती" in res["title"]
    assert "चेतावनी" == res["severity_label"]
    assert len(res["recommended_actions"]) > 0
    # Verify Devanagari script characters present
    assert any("\u0900" <= ch <= "\u097f" for ch in res["recommended_actions"][0])


def test_translate_alert_english_passthrough():
    """Verify English requests return untranslated source content."""
    res = translate_alert(
        title="Road closure at Begumpet Flyover",
        category="road_closure",
        severity="info",
        impact="Traffic diversions in effect.",
        actions=["Use alternate detour routes."],
        target_lang="en"
    )

    assert res["language"] == "en"
    assert res["title"] == "Road closure at Begumpet Flyover"
