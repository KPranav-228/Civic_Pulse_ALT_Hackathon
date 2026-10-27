"""Tests for Phase 7: Citizen Feedback, Community Confirmations & Monitoring."""

import json
import pytest
from sqlalchemy.orm import Session

from server.db.database import SessionLocal, init_db
from server.db import crud
from server.db.models import Alert
from server.scripts.merge_feedback import merge_citizen_corrections


@pytest.fixture
def db_session():
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_alert_correction_feedback(db_session: Session):
    """Verify storing user corrections for wrong category/severity."""
    # Create test alert
    alert = crud.create_alert(
        db=db_session,
        title="Unexpected low water pressure in Kondapur residential ward",
        category="other",
        severity="info",
        affected_areas=json.dumps([{"name": "Kondapur", "lat": 17.4699, "lng": 78.3578}]),
        confidence=0.75,
        needs_review=True
    )

    # Submit citizen correction
    corr = crud.create_alert_correction(
        db=db_session,
        alert_id=alert.id,
        original_category="other",
        suggested_category="water_supply",
        original_severity="info",
        suggested_severity="warning",
        comment="This is a scheduled drinking water pipeline issue, not generic other.",
        user_id="citizen_tester"
    )

    assert corr.id is not None
    assert corr.suggested_category == "water_supply"
    assert corr.suggested_severity == "warning"
    assert corr.is_merged is False

    # Check unmerged list
    unmerged = crud.get_unmerged_corrections(db=db_session)
    assert any(c.id == corr.id for c in unmerged)


def test_community_confirmation_votes(db_session: Session):
    """Verify citizen crowd-verification buttons ('Water arrived', 'Power still off')."""
    alert = crud.create_alert(
        db=db_session,
        title="Power cut in Ameerpet metro zone",
        category="power_cut",
        severity="warning",
        status="active",
        confidence=0.9
    )

    # Citizen 1 votes 'still_active'
    crud.add_community_confirmation(
        db=db_session,
        alert_id=alert.id,
        status_vote="still_active",
        user_id="user_1"
    )

    # Citizen 2 votes 'resolved' ("Power arrived")
    crud.add_community_confirmation(
        db=db_session,
        alert_id=alert.id,
        status_vote="resolved",
        user_id="user_2"
    )

    stats = crud.get_community_confirmations(db=db_session, alert_id=alert.id)
    assert stats["confirmed_resolved"] == 1
    assert stats["confirmed_active"] == 1
    assert stats["total_votes"] == 2


def test_monitoring_metrics(db_session: Session):
    """Verify model performance monitoring, false-alarm rate, and drift indicator."""
    metrics = crud.get_monitoring_metrics(db=db_session)

    assert "total_alerts" in metrics
    assert "category_distribution" in metrics
    assert "severity_distribution" in metrics
    assert "false_alarm_rate" in metrics
    assert "drift_indicator" in metrics
    assert "drift_score" in metrics
    assert metrics["drift_indicator"] in {"stable", "moderate_drift", "high_drift"}
