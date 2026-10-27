"""Tests for Phase 5: Delivery (Telegram bot, SMS fallback, Weekly Digest)."""

import pytest
from sqlalchemy.orm import Session

from server.db.database import SessionLocal, init_db
from server.services.sms_service import sms_service
from server.services.telegram_bot import telegram_bot
from server.services.digest_service import compile_weekly_digest


@pytest.fixture
def db_session():
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_sms_fallback_mock():
    """Verify mock SMS provider formats and logs messages correctly."""
    res = sms_service.send_alert_sms(
        to_phone="+919876543210",
        alert_title="Drinking water shutdown in Kukatpally",
        category="water_supply",
        severity="critical",
        actions=["Store sufficient drinking water in advance."]
    )
    assert res["success"] is True
    assert res["provider"] == "mock"
    assert "mock_sms_" in res["message_id"]


def test_telegram_bot_commands(db_session: Session):
    """Verify Telegram slash command parsing and responses."""
    user_id = "test_telegram_citizen_1"

    # 1. /start
    welcome = telegram_bot.handle_command(user_id, "/start", db=db_session)
    assert "Welcome to CivicPulse" in welcome
    assert "/setlocality" in welcome

    # 2. /setlocality
    loc_resp = telegram_bot.handle_command(user_id, "/setlocality Gachibowli X Roads", db=db_session)
    assert "Gachibowli" in loc_resp
    assert "West Zone" in loc_resp

    # 3. /addlocation
    add_resp = telegram_bot.handle_command(user_id, "/addlocation Office Hitec City", db=db_session)
    assert "Office" in add_resp
    assert "Hitec City" in add_resp

    # 4. /locations
    list_resp = telegram_bot.handle_command(user_id, "/locations", db=db_session)
    assert "Office" in list_resp
    assert "Hitec City" in list_resp

    # 5. /language
    lang_resp = telegram_bot.handle_command(user_id, "/language te", db=db_session)
    assert "Telugu" in lang_resp

    # 6. /alerts
    alerts_resp = telegram_bot.handle_command(user_id, "/alerts", db=db_session)
    assert "Active Civic Alerts" in alerts_resp or "No active disruptions" in alerts_resp


def test_weekly_digest_compilation(db_session: Session):
    """Verify weekly digest metrics and structure."""
    digest = compile_weekly_digest(db=db_session, locality="Madhapur")
    assert "period" in digest
    assert "civic_health_score" in digest
    assert "summary" in digest
    assert "active_disruptions" in digest
    assert "resolved_works" in digest
    assert digest["locality"] == "Madhapur"
    assert 0 <= digest["civic_health_score"] <= 100
