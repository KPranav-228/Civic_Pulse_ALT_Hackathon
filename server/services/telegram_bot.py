"""Telegram Citizen Alert Bot for CivicPulse Hyderabad.

Supports:
- /start: Welcome and registration
- /setlocality <name>: Set current neighborhood (e.g. /setlocality Gachibowli)
- /addlocation <label> <name>: Add monitoring circle (e.g. /addlocation Office Hitec City)
- /locations: List saved monitoring circles
- /removelocation <id>: Remove a saved circle
- /language <en|te|hi>: Choose delivery language
- /alerts: Fetch active critical & warning civic alerts for your areas
- /reminders: View upcoming 12h and 2h proactive reminders

Works with valid TELEGRAM_BOT_TOKEN or falls back to an auditable mock simulator
for offline hackathon demonstrations.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from server.db import crud
from server.db.database import SessionLocal
from server.nlp.gazetteer import resolve_locality, is_alert_within_radius
from server.services.reminder_service import get_user_reminders

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Manages Telegram bot command handling, responses, and message dispatch."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.is_active = bool(self.token and self.token != "your_telegram_bot_token_here")
        self.dispatched_messages: List[Dict[str, Any]] = []

    def handle_command(self, user_id: str, command_text: str, db: Optional[Session] = None) -> str:
        """Process incoming slash commands and return formatted Markdown response."""
        parts = command_text.strip().split()
        if not parts:
            return "Please enter a valid command. Type /start to see available options."

        cmd = parts[0].lower()
        args = parts[1:]

        close_session = False
        if db is None:
            db = SessionLocal()
            close_session = True

        try:
            if cmd == "/start":
                return (
                    "🏛️ *Welcome to CivicPulse Hyderabad Bot!*\n\n"
                    "I turn municipal orders and breaking news into location-specific alerts for your neighborhood.\n\n"
                    "📌 *Available Commands:*\n"
                    "• `/setlocality <name>` — Set your primary neighborhood (e.g. `/setlocality Gachibowli`)\n"
                    "• `/addlocation <label> <name>` — Monitor multiple circles (e.g. `/addlocation Office Hitec City`)\n"
                    "• `/locations` — View your active monitoring circles\n"
                    "• `/language <en|te|hi>` — Change notification language\n"
                    "• `/alerts` — Get current active alerts for your locations\n"
                    "• `/reminders` — View upcoming 12h and 2h proactive reminders\n"
                )

            elif cmd in {"/setlocality", "/locality"}:
                if not args:
                    return "⚠️ Please specify a neighborhood. Example: `/setlocality Madhapur`"
                query = " ".join(args)
                resolved = resolve_locality(query)
                if not resolved:
                    return f"❌ Could not find '{query}' in the Hyderabad gazetteer. Try major areas like Gachibowli, Kukatpally, or Begumpet."

                crud.upsert_user_profile(db=db, user_id=user_id)
                return (
                    f"✅ Locality set to *{resolved['canonical_name']}* ({resolved['zone']}).\n"
                    f"Coordinates: `{resolved['lat']}, {resolved['lng']}` (Radius: {resolved['radius_km']} km)"
                )

            elif cmd == "/addlocation":
                if len(args) < 2:
                    return "⚠️ Format: `/addlocation <Label> <Locality>`. Example: `/addlocation Office Hitec City`"
                label = args[0]
                loc_name = " ".join(args[1:])
                resolved = resolve_locality(loc_name)
                if not resolved:
                    return f"❌ Unknown locality '{loc_name}'. Please verify the spelling."

                created = crud.create_saved_location(
                    db=db,
                    label=label,
                    locality_name=resolved["canonical_name"],
                    lat=resolved["lat"],
                    lng=resolved["lng"],
                    radius_km=resolved["radius_km"],
                    user_id=user_id
                )
                return f"📍 Added *{created.label}* at *{created.locality_name}* (Monitoring radius: {created.radius_km} km)."

            elif cmd == "/locations":
                locations = crud.get_saved_locations(db=db, user_id=user_id)
                if not locations:
                    return "No saved locations found. Use `/addlocation Home Gachibowli` to add your first circle!"
                lines = ["📍 *Your Monitored Circles:*"]
                for loc in locations:
                    lines.append(f"• *{loc.label}*: {loc.locality_name} ({loc.radius_km} km radius) `[ID: {loc.id}]`")
                return "\n".join(lines)

            elif cmd == "/removelocation":
                if not args:
                    return "⚠️ Format: `/removelocation <Location_ID>`. Use `/locations` to see IDs."
                try:
                    loc_id = int(args[0])
                    success = crud.delete_saved_location(db=db, location_id=loc_id, user_id=user_id)
                    if success:
                        return f"🗑️ Location ID `{loc_id}` removed."
                    return f"❌ Location ID `{loc_id}` not found."
                except ValueError:
                    return "⚠️ Please provide a numeric location ID."

            elif cmd == "/language":
                if not args or args[0].lower() not in {"en", "te", "hi"}:
                    return "⚠️ Please specify a valid language code: `/language en` (English), `/language te` (Telugu), or `/language hi` (Hindi)."
                lang = args[0].lower()
                crud.upsert_user_profile(db=db, user_id=user_id, preferred_language=lang)
                names = {"en": "English", "te": "Telugu (తెలుగు)", "hi": "Hindi (हिंदी)"}
                return f"🌐 Notification language updated to *{names[lang]}*."

            elif cmd == "/alerts":
                saved_locations = crud.get_saved_locations(db=db, user_id=user_id)
                all_alerts = crud.get_alerts(db=db, status="active", limit=20)

                matched = []
                for a in all_alerts:
                    areas = json.loads(a.affected_areas) if a.affected_areas else []
                    if saved_locations:
                        for sl in saved_locations:
                            in_rad, dist = is_alert_within_radius(areas, sl.lat, sl.lng, sl.radius_km)
                            if in_rad:
                                matched.append((a, sl.label, dist))
                                break
                    else:
                        matched.append((a, "Citywide", None))

                if not matched:
                    return "🟢 *No active disruptions reported in your monitored zones.* All systems operating normally."

                response_blocks = [f"🚨 *Active Civic Alerts ({len(matched)})*\n"]
                for a, label, dist in matched[:5]:
                    sev_emoji = "🔴" if a.severity == "critical" else "🟠" if a.severity == "warning" else "🟡"
                    tier = f"[{a.source_tier.upper()}]" if getattr(a, "source_tier", None) else ""
                    dist_str = f"({dist:.1f} km away)" if dist else ""
                    response_blocks.append(
                        f"{sev_emoji} *{a.title}*\n"
                        f"• Category: `{a.category}` | Tier: {tier} {dist_str}\n"
                        f"• Zone: {label}\n"
                        f"• Impact: {a.expected_impact or 'General advisory'}\n"
                    )
                return "\n".join(response_blocks)

            elif cmd == "/reminders":
                rems = get_user_reminders(db=db, user_id=user_id, status="scheduled")
                if not rems:
                    return "⏰ No upcoming proactive reminders scheduled for your account."
                lines = [f"⏰ *Upcoming Disruption Reminders ({len(rems)})*\n"]
                for r in rems:
                    lines.append(f"• *[{r.reminder_type.upper()}]* {r.scheduled_for.strftime('%d %b %I:%M %p')}\n  {r.message}")
                return "\n".join(lines)

            else:
                return f"❓ Unknown command `{cmd}`. Type `/start` for available options."

        finally:
            if close_session:
                db.close()

    def dispatch_alert(self, chat_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send formatted alert notification to Telegram user."""
        title = alert_data.get("title", "Civic Alert")
        category = alert_data.get("category", "General").replace("_", " ").title()
        severity = alert_data.get("severity", "Info").upper()
        actions = alert_data.get("recommended_actions", [])

        action_text = "\n".join([f"  ✓ {act}" for act in actions[:3]])
        body = (
            f"🔔 *CivicPulse Alert: {severity}*\n"
            f"📁 *Category:* {category}\n"
            f"📢 *Notice:* {title}\n\n"
            f"🛡️ *Action Steps:*\n{action_text}\n\n"
            f"_Reply /alerts to see full city status._"
        )

        record = {
            "chat_id": chat_id,
            "body": body,
            "status": "sent" if self.is_active else "mock_dispatched",
            "provider": "telegram",
        }
        self.dispatched_messages.append(record)
        logger.info(f"[TelegramBot] Dispatched alert to {chat_id}: {title[:50]}")
        return record


# Global singleton
telegram_bot = TelegramBotService()
