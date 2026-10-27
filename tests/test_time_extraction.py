"""Tests for Phase 4: Structured Temporal Extraction, Reminders, and Vulnerable Modes."""

from datetime import datetime, date, timedelta, timezone
import pytest
from sqlalchemy.orm import Session

from server.nlp.time_extractor import (
    extract_temporal_fields,
    extract_temporal_range,
    extract_incident_date,
)
from server.services.reminder_service import compute_scheduled_reminders
from server.services.personalization import compute_effective_severity


def test_time_range_extraction():
    """Verify extraction of 12h AM/PM and 24h ranges."""
    # 1. 9 AM to 5 PM
    t1, t2 = extract_temporal_range("Scheduled power shutdown from 9 AM to 5 PM in Madhapur.")
    assert t1 is not None and t2 is not None
    assert t1.hour == 9 and t1.minute == 0
    assert t2.hour == 17 and t2.minute == 0

    # 2. 10:00 to 14:00
    t1, t2 = extract_temporal_range("Water supply disruption from 10:00 to 14:00 hrs tomorrow.")
    assert t1 is not None and t2 is not None
    assert t1.hour == 10 and t2.hour == 14

    # 3. 10am - 2pm
    t1, t2 = extract_temporal_range("Pipeline maintenance between 10am - 2pm.")
    assert t1 is not None and t2 is not None
    assert t1.hour == 10 and t2.hour == 14


def test_relative_date_and_duration():
    """Verify relative date resolution and duration calculation."""
    ref_dt = datetime(2026, 10, 26, 8, 0, 0, tzinfo=timezone.utc)

    # "tomorrow from 9 AM to 5 PM"
    res = extract_temporal_fields("Power outage tomorrow from 9 AM to 5 PM in Gachibowli", reference_datetime=ref_dt)
    assert res["duration_hours"] == 8.0
    assert res["incident_date"] == "2026-10-27"
    assert res["start_time"] is not None
    assert res["start_time"].day == 27
    assert res["start_time"].hour == 9
    assert res["expected_end_time"].hour == 17


def test_scheduled_reminders_computation():
    """Verify 12h and 2h proactive reminder slot generation."""
    ref_now = datetime(2026, 10, 26, 8, 0, 0, tzinfo=timezone.utc)
    # Event starting tomorrow at 9 AM (25 hours ahead)
    event_start = ref_now + timedelta(hours=25)

    rems = compute_scheduled_reminders(
        alert_id=101,
        title="Scheduled Power Shutdown",
        start_time=event_start,
        user_id="citizen_1",
        now=ref_now
    )

    types = [r["reminder_type"] for r in rems]
    assert "12h" in types
    assert "2h" in types

    # Verify scheduled times
    r12 = next(r for r in rems if r["reminder_type"] == "12h")
    r2 = next(r for r in rems if r["reminder_type"] == "2h")
    assert r12["scheduled_for"] == event_start - timedelta(hours=12)
    assert r2["scheduled_for"] == event_start - timedelta(hours=2)


def test_vulnerable_user_modes_severity_elevation():
    """Verify vulnerable modes elevate power-cut alerts to critical."""
    # 1. Dialysis patient facing scheduled power outage
    eff_sev, reason = compute_effective_severity(
        base_severity="advisory",
        category="power_cut",
        vulnerable_modes=["dialysis"]
    )
    assert eff_sev == "critical"
    assert "medical life support" in reason.lower()

    # 2. Medical home oxygen facing warning power cut
    eff_sev, reason = compute_effective_severity(
        base_severity="warning",
        category="power_cut",
        vulnerable_modes=["home_oxygen"]
    )
    assert eff_sev == "critical"

    # 3. Elderly living alone facing info outage
    eff_sev, reason = compute_effective_severity(
        base_severity="info",
        category="power_cut",
        vulnerable_modes=["elderly"]
    )
    assert eff_sev == "warning"
    assert "elderly" in reason.lower()

    # 4. Standard user with no vulnerable modes maintains base severity
    eff_sev, reason = compute_effective_severity(
        base_severity="advisory",
        category="power_cut",
        vulnerable_modes=[]
    )
    assert eff_sev == "advisory"
    assert reason is None
