"""Unit tests for Phase 2: Trust, source credibility tiering, update/cancellation handling."""

import json
from datetime import datetime
import pytest
from sqlalchemy.orm import Session

from server.db.database import SessionLocal, init_db
from server.db.models import Alert
from server.schemas.alert import AlertBase, AlertResponse, AlertUpdate
from server.services.pipeline import resolve_source_tier, detect_status_and_event_link, process_report_pipeline


@pytest.fixture
def db_session():
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_resolve_source_tier():
    """Verify classification of sources into official, news, and unverified tiers."""
    # Official authorities
    assert resolve_source_tier("GHMC Disaster Response", "Waterlogging cleared") == "official"
    assert resolve_source_tier("HMWSSB", "Pipeline repair scheduled") == "official"
    assert resolve_source_tier("Hyderabad Traffic Police", "Traffic diversion at Begumpet") == "official"
    assert resolve_source_tier("TGSPDCL", "Substation maintenance") == "official"
    assert resolve_source_tier(None, "GHMC official release: emergency tree removal") == "official"

    # News outlets
    assert resolve_source_tier("The Hindu", "Heavy rains hit Hyderabad outskirts") == "news"
    assert resolve_source_tier("Deccan Chronicle", "Road repairs completed") == "news"
    assert resolve_source_tier("Telangana Today", "Water tanker supplies increased") == "news"

    # Unverified / crowd
    assert resolve_source_tier("Random Twitter User", "Seeing lots of smoke near Hitec city") == "unverified"
    assert resolve_source_tier(None, "Heard there is a water shutdown tomorrow") == "unverified"


def test_update_cancellation_linking(db_session: Session):
    """Verify that update/cancellation reports link to prior alerts and mark them resolved."""
    # 1. Create an active original alert in Madhapur
    orig_alert = Alert(
        title="Major pipeline rupture in Madhapur disrupts water supply",
        category="water_supply",
        severity="critical",
        status="active",
        affected_areas=json.dumps([{"name": "Madhapur", "lat": 17.4483, "lng": 78.3915}]),
        source_name="HMWSSB",
        source_tier="official",
        confidence=0.92,
        needs_review=False
    )
    db_session.add(orig_alert)
    db_session.commit()
    db_session.refresh(orig_alert)

    orig_id = orig_alert.id
    assert orig_alert.status == "active"

    # 2. Process an update notice stating water supply is restored
    restoration_text = "HMWSSB Update: Water supply has been successfully restored in Madhapur after pipeline repair."
    status, parent_id = detect_status_and_event_link(
        raw_text=restoration_text,
        affected_areas=[{"name": "Madhapur"}],
        category="water_supply",
        db=db_session
    )

    assert status == "resolved"
    assert parent_id == orig_id

    # Verify original alert status was updated in DB
    refreshed_orig = db_session.query(Alert).filter(Alert.id == orig_id).first()
    assert refreshed_orig.status == "resolved"


def test_schema_trust_fields():
    """Verify Pydantic models validate source_tier, parent_alert_id, and status."""
    payload = {
        "title": "Road barricaded for metro construction",
        "category": "road_closure",
        "severity": "advisory",
        "source_tier": "official",
        "status": "updated",
        "parent_alert_id": 42,
        "confidence": 0.85,
        "source_name": "Traffic Police"
    }
    schema = AlertBase(**payload)
    assert schema.source_tier == "official"
    assert schema.parent_alert_id == 42

    # Invalid source_tier rejection
    with pytest.raises(Exception):
        AlertBase(**{**payload, "source_tier": "unknown_tier"})
