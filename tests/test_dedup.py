"""Unit tests for report clustering and deduplication logic."""

import pytest
from server.nlp.clustering import find_duplicate_reports


def test_near_duplicate_clustering():
    report_a = "Traffic blocked under Begumpet flyover due to heavy waterlogging. Police advising detour."
    report_b = "Heavy waterlogging under Begumpet flyover has blocked traffic. Commuters advised to take detour."
    report_c = "Scheduled 4-hour power cut announced for residential areas in Whitefield tomorrow."

    clusters = find_duplicate_reports([report_a, report_b, report_c], similarity_threshold=0.60)
    assert len(clusters) == 1
    assert set(clusters[0]) == {0, 1}


def test_no_duplicate_distinct_reports():
    report_a = "School closure ordered in Hyderabad due to heavy rainfall."
    report_b = "Water pipeline maintenance scheduled for Indiranagar on Wednesday."
    report_c = "Pulse polio immunization camp to be conducted at primary health centers."

    clusters = find_duplicate_reports([report_a, report_b, report_c], similarity_threshold=0.70)
    assert len(clusters) == 0


@pytest.fixture
def db_session():
    from server.db.database import SessionLocal, init_db
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_check_duplicate_alert_exact_and_similarity(db_session):
    from server.db.models import Alert
    from server.services.pipeline import check_duplicate_alert

    existing_alert = Alert(
        title="Waterlogging under Begumpet flyover",
        category="road_closure",
        severity="warning",
        status="active",
        source_url="https://telanganatoday.com/traffic-begumpet-unique-test",
        preprocessed_text="traffic blocked begumpet flyover heavy waterlogging police advise detour",
        expected_impact="Severe traffic jams expected under Begumpet flyover"
    )
    db_session.add(existing_alert)
    db_session.commit()
    db_session.refresh(existing_alert)

    try:
        # Test 1: URL match
        dup_url = check_duplicate_alert(
            raw_text="Different headline text but same article link",
            cleaned_text="different headline text but same article link",
            predicted_category="road_closure",
            source_url="https://telanganatoday.com/traffic-begumpet-unique-test",
            db=db_session
        )
        assert dup_url is not None
        assert dup_url.id == existing_alert.id

        # Test 2: Near-duplicate text similarity match in same category
        dup_sim = check_duplicate_alert(
            raw_text="Heavy waterlogging under Begumpet flyover has blocked traffic. Commuters advised to take detour.",
            cleaned_text="heavy waterlogging under begumpet flyover has blocked traffic commuters advised take detour",
            predicted_category="road_closure",
            source_url=None,
            db=db_session
        )
        assert dup_sim is not None
        assert dup_sim.id == existing_alert.id

        # Test 3: Unrelated incident in different category should NOT be flagged as duplicate of this
        no_dup = check_duplicate_alert(
            raw_text="Scheduled power outage in Madhapur tomorrow for substation maintenance work.",
            cleaned_text="scheduled power outage in madhapur tomorrow for substation maintenance work",
            predicted_category="power_cut",
            source_url=None,
            db=db_session
        )
        assert no_dup is None or no_dup.id != existing_alert.id
    finally:
        db_session.delete(existing_alert)
        db_session.commit()


