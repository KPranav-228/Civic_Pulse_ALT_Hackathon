"""Unit tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError
from server.schemas.alert import AlertBase, ClassifyRequest, IngestRequest


def test_valid_alert_schema():
    payload = {
        "title": "Severe road waterlogging under Begumpet flyover",
        "category": "road_closure",
        "severity": "warning",
        "affected_areas": [{"name": "Begumpet", "lat": 17.44, "lng": 78.46}],
        "expected_impact": "Traffic movement halted across arterial lanes.",
        "recommended_actions": ["Avoid Begumpet flyover", "Use bypass route"],
        "confidence": 0.92,
        "needs_review": False
    }
    alert = AlertBase(**payload)
    assert alert.title == payload["title"]
    assert alert.category == "road_closure"
    assert len(alert.affected_areas) == 1
    assert alert.confidence == 0.92


def test_invalid_category_rejection():
    with pytest.raises(ValidationError):
        AlertBase(
            title="Invalid category test",
            category="alien_invasion",  # Not in allowed enum
            severity="critical"
        )


def test_ingest_request_validation():
    # Valid with text
    req1 = IngestRequest(text="Pipeline burst affecting drinking water supply in Kukatpally.")
    assert req1.text is not None

    # Valid with url
    req2 = IngestRequest(url="https://thehindu.com/news/hyderabad/traffic-update")
    assert req2.url is not None

    # Invalid without either
    with pytest.raises(ValidationError):
        IngestRequest()


def test_classify_request_length():
    # Too short text
    with pytest.raises(ValidationError):
        ClassifyRequest(text="short")
