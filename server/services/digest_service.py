"""Weekly Civic Digest Service for CivicPulse Hyderabad.

Synthesizes weekly municipal activity, resolved infrastructure works,
upcoming scheduled maintenance, and civic health metrics into a concise citizen brief.
"""

from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from server.db.models import Alert, Topic
from server.nlp.gazetteer import is_alert_within_radius, resolve_locality


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def compile_weekly_digest(
    db: Session,
    locality: Optional[str] = None,
    user_id: str = "default_user"
) -> Dict[str, Any]:
    """Generate a comprehensive weekly infrastructure & civic digest."""
    now = _utcnow()
    seven_days_ago = now - timedelta(days=7)

    # 1. Fetch recent alerts from past 7 days
    recent_alerts = (
        db.query(Alert)
        .filter(Alert.created_at >= seven_days_ago)
        .order_by(Alert.created_at.desc())
        .all()
    )

    # Resolve locality if supplied
    loc_meta = resolve_locality(locality) if locality else None

    filtered_alerts = []
    for a in recent_alerts:
        if loc_meta:
            areas = json.loads(a.affected_areas) if a.affected_areas else []
            in_range, _ = is_alert_within_radius(areas, loc_meta["lat"], loc_meta["lng"], loc_meta["radius_km"])
            if in_range:
                filtered_alerts.append(a)
        else:
            filtered_alerts.append(a)

    # 2. Categorize metrics
    total_count = len(filtered_alerts)
    active_count = sum(1 for a in filtered_alerts if a.status == "active")
    resolved_count = sum(1 for a in filtered_alerts if a.status in {"resolved", "past", "cancelled"})

    by_category: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    for a in filtered_alerts:
        by_category[a.category] = by_category.get(a.category, 0) + 1
        by_severity[a.severity] = by_severity.get(a.severity, 0) + 1

    # 3. Key highlights (resolved vs active)
    active_highlights = [
        {
            "id": a.id,
            "title": a.title,
            "category": a.category,
            "severity": a.severity,
            "expected_impact": a.expected_impact
        }
        for a in filtered_alerts if a.status == "active"
    ][:5]

    resolved_highlights = [
        {
            "id": a.id,
            "title": a.title,
            "category": a.category,
            "status": a.status
        }
        for a in filtered_alerts if a.status in {"resolved", "cancelled"}
    ][:5]

    # 4. Top topics
    topics = db.query(Topic).order_by(Topic.created_at.desc()).limit(3).all()
    topic_keywords = []
    for t in topics:
        kw = json.loads(t.keywords) if isinstance(t.keywords, str) else (t.keywords or [])
        topic_keywords.append(", ".join(kw[:5]))

    # 5. Citizen Infrastructure Health Rating (0-100)
    # Fewer critical disruptions = higher civic score
    critical_count = by_severity.get("critical", 0)
    civic_health_score = max(30, 100 - (critical_count * 15) - (active_count * 5))

    return {
        "period": f"{seven_days_ago.strftime('%d %b %Y')} to {now.strftime('%d %b %Y')}",
        "locality": loc_meta["canonical_name"] if loc_meta else "Greater Hyderabad",
        "zone": loc_meta["zone"] if loc_meta else "Citywide",
        "civic_health_score": civic_health_score,
        "summary": {
            "total_reports": total_count,
            "active_disruptions": active_count,
            "resolved_restorations": resolved_count,
            "by_category": by_category,
            "by_severity": by_severity
        },
        "active_disruptions": active_highlights,
        "resolved_works": resolved_highlights,
        "recurring_civic_topics": topic_keywords,
        "weekly_guidance": "Verify water tank levels on Tuesdays & Saturdays; check TGSPDCL grid schedule before peak WFH hours."
    }
