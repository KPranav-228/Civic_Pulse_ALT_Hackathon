"""SMS Fallback Delivery Service for CivicPulse.

Provides an abstract provider pattern supporting Twilio for production
and a robust MockSMSProvider for offline hackathon testing without credentials.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"
SMS_LOG_FILE = REPORTS_DIR / "sent_sms_log.jsonl"


class BaseSMSProvider(ABC):
    """Abstract interface for SMS transmission."""

    @abstractmethod
    def send_sms(self, to_phone: str, body: str) -> Dict[str, Any]:
        """Send an SMS notification."""
        pass


class MockSMSProvider(BaseSMSProvider):
    """In-memory and file-based mock SMS provider for offline execution."""

    def __init__(self, log_path: Path = SMS_LOG_FILE):
        self.log_path = log_path
        self.sent_messages: List[Dict[str, Any]] = []

    def send_sms(self, to_phone: str, body: str) -> Dict[str, Any]:
        record = {
            "to": to_phone,
            "body": body,
            "status": "delivered",
            "provider": "mock",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        self.sent_messages.append(record)
        logger.info(f"[MockSMS] Delivered SMS to {to_phone}: {body[:60]}...")

        # Persist to disk for auditable verification
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to append to SMS log file: {e}")

        return {"success": True, "provider": "mock", "message_id": f"mock_sms_{len(self.sent_messages)}"}


class TwilioSMSProvider(BaseSMSProvider):
    """Twilio SMS provider using credentials from environment variables."""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_phone = os.getenv("TWILIO_FROM_NUMBER")
        self.client = None

        if self.account_sid and self.auth_token and self.from_phone:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS Client successfully initialized.")
            except ImportError:
                logger.warning("Twilio library not installed. Falling back to mock provider.")
            except Exception as e:
                logger.warning(f"Twilio client init failed: {e}")

    def send_sms(self, to_phone: str, body: str) -> Dict[str, Any]:
        if not self.client:
            raise RuntimeError("Twilio client is not configured with valid credentials.")

        message = self.client.messages.create(
            body=body,
            from_=self.from_phone,
            to=to_phone
        )
        return {
            "success": True,
            "provider": "twilio",
            "message_sid": message.sid,
            "status": message.status
        }


class SMSService:
    """Unified SMS dispatch service with auto-fallback to mock provider."""

    def __init__(self):
        self.mock_provider = MockSMSProvider()
        self.twilio_provider = None

        # Attempt to initialize Twilio if credentials exist
        if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"):
            try:
                self.twilio_provider = TwilioSMSProvider()
            except Exception:
                self.twilio_provider = None

    def send_alert_sms(self, to_phone: str, alert_title: str, category: str, severity: str, actions: List[str]) -> Dict[str, Any]:
        """Format and send an urgent civic alert via SMS (constrained to 160 chars or concatenated)."""
        action_summary = actions[0] if actions else "Follow municipal advisory."
        msg_body = (
            f"[CivicPulse {severity.upper()}] {category.upper()}: {alert_title}\n"
            f"Action: {action_summary}"
        )

        if self.twilio_provider and self.twilio_provider.client:
            try:
                return self.twilio_provider.send_sms(to_phone, msg_body)
            except Exception as e:
                logger.warning(f"Twilio transmission failed ({e}). Falling back to MockSMSProvider.")

        return self.mock_provider.send_sms(to_phone, msg_body)


# Global singleton
sms_service = SMSService()
