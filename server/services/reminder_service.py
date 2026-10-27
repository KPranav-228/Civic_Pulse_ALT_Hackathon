"""Proactive Scheduled Reminders for CivicPulse Alerts.

Generates and schedules reminders 12 hours and 2 hours before scheduled disruptions
(e.g., scheduled power cuts, water supply shutdowns, and planned road closures).
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from server.db.models import Alert, AlertReminder


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def compute_scheduled_reminders(
    alert_id: int,
    title: str,
    start_time: datetime,
    user_id: str = "default_user",
    now: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Determine scheduled reminder slots (12h, 2h before, or immediate) for an alert."""
    current_time = now or _utcnow()

    # Ensure timezone awareness
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)

    reminders = []

    # 1. 12-hour reminder
    time_12h = start_time - timedelta(hours=12)
    if time_12h > current_time:
        reminders.append({
            "alert_id": alert_id,
            "user_id": user_id,
            "reminder_type": "12h",
            "scheduled_for": time_12h,
            "status": "scheduled",
            "channel": "in_app",
            "message": f"Upcoming in 12h: {title} starts at {start_time.strftime('%I:%M %p')}. Complete preparations in advance."
        })

    # 2. 2-hour reminder
    time_2h = start_time - timedelta(hours=2)
    if time_2h > current_time:
        reminders.append({
            "alert_id": alert_id,
            "user_id": user_id,
            "reminder_type": "2h",
            "scheduled_for": time_2h,
            "status": "scheduled",
            "channel": "in_app",
            "message": f"URGENT (2h remaining): {title} begins at {start_time.strftime('%I:%M %p')}. Finalize essential backups."
        })

    # 3. If event starts within 2 hours or is ongoing
    if not reminders and start_time >= current_time:
        reminders.append({
            "alert_id": alert_id,
            "user_id": user_id,
            "reminder_type": "immediate",
            "scheduled_for": current_time,
            "status": "scheduled",
            "channel": "in_app",
            "message": f"IMMEDIATE ADVISORY: {title} starts shortly at {start_time.strftime('%I:%M %p')}."
        })

    return reminders


def schedule_reminders_for_alert(
    db: Session,
    alert_id: int,
    user_id: str = "default_user"
) -> List[AlertReminder]:
    """Schedule 12h and 2h reminders in the database for a civic alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert or not alert.start_time:
        return []

    # Check if reminders already scheduled for this alert and user
    existing = (
        db.query(AlertReminder)
        .filter(AlertReminder.alert_id == alert_id, AlertReminder.user_id == user_id)
        .all()
    )
    if existing:
        return existing

    computed = compute_scheduled_reminders(
        alert_id=alert.id,
        title=alert.title,
        start_time=alert.start_time,
        user_id=user_id
    )

    created_records = []
    for r_data in computed:
        rec = AlertReminder(
            alert_id=r_data["alert_id"],
            user_id=r_data["user_id"],
            reminder_type=r_data["reminder_type"],
            scheduled_for=r_data["scheduled_for"],
            status=r_data["status"],
            channel=r_data["channel"],
            message=r_data["message"]
        )
        db.add(rec)
        created_records.append(rec)

    db.commit()
    for rec in created_records:
        db.refresh(rec)

    return created_records


def get_user_reminders(
    db: Session,
    user_id: str = "default_user",
    status: Optional[str] = None
) -> List[AlertReminder]:
    """Fetch active reminders for a citizen."""
    q = db.query(AlertReminder).filter(AlertReminder.user_id == user_id)
    if status:
        q = q.filter(AlertReminder.status == status)
    return q.order_by(AlertReminder.scheduled_for.asc()).all()


def cancel_reminder(db: Session, reminder_id: int, user_id: str = "default_user") -> bool:
    """Cancel a scheduled reminder."""
    rec = (
        db.query(AlertReminder)
        .filter(AlertReminder.id == reminder_id, AlertReminder.user_id == user_id)
        .first()
    )
    if not rec:
        return False
    rec.status = "cancelled"
    db.commit()
    return True
