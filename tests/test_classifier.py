"""Unit tests for category and severity classifier inference."""

import pytest
from server.nlp.classifiers import model_suite


@pytest.fixture(scope="module", autouse=True)
def ensure_models():
    if model_suite.vectorizer is None:
        model_suite.load_artifacts()


def test_road_closure_classification():
    text = "Traffic movement completely blocked along Outer Ring Road flyover due to multi-vehicle collision."
    pred = model_suite.predict(text)
    assert pred["category"] == "road_closure"
    assert pred["category_confidence"] > 0.5


def test_power_cut_classification():
    text = "Scheduled power supply interruption in Ameerpet from 10 AM to 4 PM due to transformer upgrade."
    pred = model_suite.predict(text)
    assert pred["category"] == "power_cut"
    assert pred["category_confidence"] > 0.5


def test_severe_weather_classification():
    text = "Red alert issued for Chennai: Extremely heavy rainfall and gusty storm winds forecast for next 24 hours."
    pred = model_suite.predict(text)
    assert pred["category"] == "severe_weather"
    assert pred["severity"] in ["warning", "critical"]


def test_cloudburst_waterlogging_raises_severe_weather():
    text = "Severe cloudburst waterlogging halts vehicular traffic along Gachibowli Outer Ring Road junction."
    pred = model_suite.predict(text)
    assert pred["category"] == "severe_weather"
    assert "road_closure" in pred.get("secondary_categories", []) or pred["category_confidence"] >= 0.85


def test_secondary_weather_tags_detected():
    text = "Traffic diverted around underpass due to heavy rainfall and localized waterlogging."
    pred = model_suite.predict(text)
    assert pred["category"] == "severe_weather" or "severe_weather" in pred.get("secondary_categories", [])

