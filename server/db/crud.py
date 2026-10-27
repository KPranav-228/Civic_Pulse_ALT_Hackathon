"""
CRUD (Create / Read / Update) helpers for CivicPulse ORM models.

Every public function accepts a SQLAlchemy ``Session`` as the first argument
and returns ORM model instances.  All writes are committed inside the
function so callers don't need to manage transactions.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from server.db.models import (
    Alert,
    Area,
    Report,
    Topic,
    SavedLocation,
    UserProfile,
    AlertCorrection,
    CommunityConfirmation,
)
from server.nlp.gazetteer import is_alert_within_radius, haversine_distance



# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def create_report(
    db: Session,
    raw_text: str,
    source_url: str | None = None,
    source_name: str | None = None,
    source_type: str = "manual",
    is_spam: bool = False,
    spam_probability: float = 0.0,
) -> Report:
    """Persist a new raw-text report.

    Args:
        db: Active database session.
        raw_text: The full text content of the report.
        source_url: URL where the report was found.
        source_name: Human-readable source label.
        source_type: One of ``rss``, ``manual``, or ``url``.
        is_spam: Whether the report was flagged as spam.
        spam_probability: Model-assigned spam probability.

    Returns:
        The newly created ``Report`` instance (refreshed from the DB).
    """
    report = Report(
        raw_text=raw_text,
        source_url=source_url,
        source_name=source_name,
        source_type=source_type,
        is_spam=is_spam,
        spam_probability=spam_probability,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


# ---------------------------------------------------------------------------
# Alert
# ---------------------------------------------------------------------------

def create_alert(db: Session, **kwargs: Any) -> Alert:
    """Create a single alert from keyword arguments.

    Args:
        db: Active database session.
        **kwargs: Column values forwarded to the ``Alert`` constructor.

    Returns:
        The newly created ``Alert`` instance.
    """
    alert = Alert(**kwargs)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_alerts(
    db: Session,
    area: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    source_tier: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Alert]:
    """Retrieve alerts with optional filtering, pagination, and ordering.

    Supports both area keyword substring matching and radius-based
    Haversine distance matching when ``lat``, ``lng``, and ``radius_km`` are provided.
    """
    query = db.query(Alert)

    CITYWIDE_ALIASES = {
        "", "all", "all hyderabad", "overall hyderabad", "citywide",
        "all hyderabad localities", "overall hyderabad (all zones)",
        "hyderabad", "entire city", "all areas"
    }

    if area and area.strip().lower() not in CITYWIDE_ALIASES and (lat is None or lng is None):
        query = query.filter(Alert.affected_areas.ilike(f"%{area.strip()}%"))
    if category:
        query = query.filter(Alert.category == category)
    if severity:
        query = query.filter(Alert.severity == severity)
    if status:
        query = query.filter(Alert.status == status)
    if source_tier:
        query = query.filter(Alert.source_tier == source_tier)

    # If spatial radius filtering requested
    if lat is not None and lng is not None and radius_km is not None:
        # Fetch candidate alerts
        candidates = query.order_by(Alert.created_at.desc()).limit(150).all()
        matched: list[Alert] = []
        for a in candidates:
            if not a.affected_areas:
                continue
            try:
                areas = json.loads(a.affected_areas)
                if isinstance(areas, list):
                    in_range, _ = is_alert_within_radius(areas, lat, lng, radius_km)
                    if in_range:
                        matched.append(a)
            except Exception:
                continue
        return matched[skip : skip + limit]

    return (
        query.order_by(Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_alert(db: Session, alert_id: int) -> Alert | None:
    """Fetch a single alert by primary key.

    Args:
        db: Active database session.
        alert_id: The alert's integer ID.

    Returns:
        The ``Alert`` if found, otherwise ``None``.
    """
    return db.query(Alert).filter(Alert.id == alert_id).first()


def update_alert(db: Session, alert_id: int, **kwargs: Any) -> Alert | None:
    """Update an existing alert's columns.

    Args:
        db: Active database session.
        alert_id: The alert's integer ID.
        **kwargs: Column names and their new values.

    Returns:
        The updated ``Alert``, or ``None`` if not found.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        return None

    for key, value in kwargs.items():
        if hasattr(alert, key):
            setattr(alert, key, value)

    db.commit()
    db.refresh(alert)
    return alert


def get_review_queue(db: Session) -> list[Alert]:
    """Return alerts that need human review.

    An alert is reviewable when ``needs_review`` is ``True`` **or**
    ``confidence`` is below 0.5.

    Returns:
        List of ``Alert`` instances ordered by confidence ascending.
    """
    return (
        db.query(Alert)
        .filter(
            or_(
                Alert.needs_review == True,  # noqa: E712 – SQLAlchemy requires ==
                Alert.confidence < 0.5,
            )
        )
        .order_by(Alert.confidence.asc())
        .all()
    )


def bulk_create_alerts(db: Session, alerts_data: list[dict[str, Any]]) -> list[Alert]:
    """Create multiple alerts in a single transaction.

    Args:
        db: Active database session.
        alerts_data: List of dicts whose keys map to ``Alert`` columns.

    Returns:
        List of the newly persisted ``Alert`` instances.
    """
    alerts: list[Alert] = []
    for data in alerts_data:
        alert = Alert(**data)
        db.add(alert)
        alerts.append(alert)

    db.commit()
    for alert in alerts:
        db.refresh(alert)
    return alerts


# ---------------------------------------------------------------------------
# Area
# ---------------------------------------------------------------------------

def get_areas(db: Session) -> list[Area]:
    """Return all known geographic areas.

    Returns:
        List of ``Area`` instances ordered by name.
    """
    return db.query(Area).order_by(Area.name).all()


def create_area(
    db: Session,
    name: str,
    city: str,
    lat: float | None = None,
    lng: float | None = None,
) -> Area:
    """Create a new geographic area record if it does not already exist.

    Args:
        db: Active database session.
        name: Area name (must be unique).
        city: City the area belongs to.
        lat: Latitude coordinate.
        lng: Longitude coordinate.

    Returns:
        The ``Area`` instance (newly created or existing).
    """
    existing = db.query(Area).filter(Area.name == name).first()
    if existing:
        return existing
    area = Area(name=name, city=city, lat=lat, lng=lng)
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


# ---------------------------------------------------------------------------
# Topic
# ---------------------------------------------------------------------------

def create_topic(
    db: Session,
    method: str,
    keywords: str,
    coherence_score: float | None = None,
    document_count: int = 0,
) -> Topic:
    """Create a new topic cluster record.

    Args:
        db: Active database session.
        method: Clustering method used (``lda`` or ``kmeans``).
        keywords: JSON-serialised list of top keywords.
        coherence_score: Topic coherence metric (optional).
        document_count: Number of documents assigned to this topic.

    Returns:
        The newly created ``Topic`` instance.
    """
    topic = Topic(
        method=method,
        keywords=keywords,
        coherence_score=coherence_score,
        document_count=document_count,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def get_topics(db: Session) -> list[Topic]:
    """Return all topic clusters.

    Returns:
        List of ``Topic`` instances ordered by creation date descending.
    """
    return db.query(Topic).order_by(Topic.created_at.desc()).all()


# ---------------------------------------------------------------------------
# Saved Locations
# ---------------------------------------------------------------------------

def get_saved_locations(db: Session, user_id: str = "default_user") -> list[SavedLocation]:
    """Retrieve all saved locations for a citizen ordered by creation date."""
    return (
        db.query(SavedLocation)
        .filter(SavedLocation.user_id == user_id)
        .order_by(SavedLocation.created_at.asc())
        .all()
    )


def create_saved_location(
    db: Session,
    label: str,
    locality_name: str,
    lat: float,
    lng: float,
    radius_km: float = 5.0,
    user_id: str = "default_user",
) -> SavedLocation:
    """Create a new saved locality with label and monitoring radius."""
    loc = SavedLocation(
        user_id=user_id,
        label=label,
        locality_name=locality_name,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def delete_saved_location(db: Session, location_id: int, user_id: str = "default_user") -> bool:
    """Delete a saved location by ID."""
    loc = (
        db.query(SavedLocation)
        .filter(SavedLocation.id == location_id, SavedLocation.user_id == user_id)
        .first()
    )
    if not loc:
        return False
    db.delete(loc)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# User Profile
# ---------------------------------------------------------------------------

def get_user_profile(db: Session, user_id: str = "default_user") -> UserProfile:
    """Fetch user profile with household personalization preferences, creating default if absent."""
    prof = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not prof:
        prof = UserProfile(
            user_id=user_id,
            water_source="municipal",
            housing_type="apartment",
            vulnerable_modes=json.dumps([]),
            preferred_language="en",
        )
        db.add(prof)
        db.commit()
        db.refresh(prof)
    return prof


def upsert_user_profile(
    db: Session,
    user_id: str = "default_user",
    water_source: str | None = None,
    housing_type: str | None = None,
    vulnerable_modes: list[str] | None = None,
    preferred_language: str | None = None,
) -> UserProfile:
    """Upsert citizen personalization settings."""
    prof = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not prof:
        prof = UserProfile(user_id=user_id)
        db.add(prof)

    if water_source is not None:
        prof.water_source = water_source
    if housing_type is not None:
        prof.housing_type = housing_type
    if vulnerable_modes is not None:
        prof.vulnerable_modes = json.dumps(vulnerable_modes)
    if preferred_language is not None:
        prof.preferred_language = preferred_language

    db.commit()
    db.refresh(prof)
    return prof


# ---------------------------------------------------------------------------
# Citizen Feedback & Model Corrections
# ---------------------------------------------------------------------------

def create_alert_correction(
    db: Session,
    alert_id: int,
    original_category: str,
    original_severity: str,
    suggested_category: str | None = None,
    suggested_severity: str | None = None,
    comment: str | None = None,
    user_id: str = "default_user",
) -> AlertCorrection:
    """Record citizen correction for wrong severity or category."""
    corr = AlertCorrection(
        alert_id=alert_id,
        user_id=user_id,
        original_category=original_category,
        suggested_category=suggested_category,
        original_severity=original_severity,
        suggested_severity=suggested_severity,
        comment=comment,
        is_merged=False,
    )
    db.add(corr)
    db.commit()
    db.refresh(corr)
    return corr


def get_unmerged_corrections(db: Session) -> list[AlertCorrection]:
    """Retrieve all corrections that have not yet been merged into training data."""
    return db.query(AlertCorrection).filter(AlertCorrection.is_merged == False).all()


def mark_corrections_merged(db: Session, ids: list[int]) -> int:
    """Mark a list of correction IDs as successfully merged into training set."""
    if not ids:
        return 0
    updated = (
        db.query(AlertCorrection)
        .filter(AlertCorrection.id.in_(ids))
        .update({AlertCorrection.is_merged: True}, synchronize_session=False)
    )
    db.commit()
    return updated


# ---------------------------------------------------------------------------
# Community Confirmations ("Water arrived", "Power still off")
# ---------------------------------------------------------------------------

def add_community_confirmation(
    db: Session,
    alert_id: int,
    status_vote: str,  # "resolved" | "still_active"
    user_id: str = "default_user",
) -> CommunityConfirmation:
    """Record a crowd confirmation vote for ground-truth verification."""
    # Remove prior vote if user is updating vote
    prior = (
        db.query(CommunityConfirmation)
        .filter(
            CommunityConfirmation.alert_id == alert_id,
            CommunityConfirmation.user_id == user_id,
        )
        .first()
    )
    if prior:
        prior.status_vote = status_vote
        db.commit()
        db.refresh(prior)
        return prior

    conf = CommunityConfirmation(
        alert_id=alert_id,
        user_id=user_id,
        status_vote=status_vote,
    )
    db.add(conf)
    db.commit()
    db.refresh(conf)
    return conf


def get_community_confirmations(db: Session, alert_id: int) -> dict[str, int]:
    """Return aggregated count of resolved vs still_active votes for an alert."""
    votes = (
        db.query(CommunityConfirmation)
        .filter(CommunityConfirmation.alert_id == alert_id)
        .all()
    )
    resolved_count = sum(1 for v in votes if v.status_vote == "resolved")
    active_count = sum(1 for v in votes if v.status_vote == "still_active")
    return {
        "confirmed_resolved": resolved_count,
        "confirmed_active": active_count,
        "total_votes": len(votes),
    }


# ---------------------------------------------------------------------------
# Monitoring Metrics & Data Drift Indicator
# ---------------------------------------------------------------------------

def get_monitoring_metrics(db: Session) -> dict[str, Any]:
    """Compute prediction distribution, user false-alarm rate, and drift indicator."""
    from collections import Counter

    alerts = db.query(Alert).all()
    total_alerts = len(alerts)
    if total_alerts == 0:
        return {
            "total_alerts": 0,
            "category_distribution": {},
            "severity_distribution": {},
            "false_alarm_rate": 0.0,
            "drift_indicator": "stable",
            "drift_score": 0.0,
        }

    cats = [a.category for a in alerts]
    sevs = [a.severity for a in alerts]

    cat_counts = dict(Counter(cats))
    sev_counts = dict(Counter(sevs))

    # User corrections / false alarms
    corrections = db.query(AlertCorrection).all()
    total_corrections = len(corrections)
    false_alarm_rate = round(total_corrections / max(1, total_alerts), 4)

    # Reference distribution from training set (6 classes roughly uniform ~16.6%)
    ref_prob = 1.0 / 6.0
    # Current inference distribution
    drift_score = 0.0
    for c_count in cat_counts.values():
        p = c_count / total_alerts
        drift_score += abs(p - ref_prob)
    drift_score = round(drift_score / 2.0, 3)

    drift_status = "stable" if drift_score < 0.25 else "moderate_drift" if drift_score < 0.50 else "high_drift"

    return {
        "total_alerts": total_alerts,
        "category_distribution": cat_counts,
        "severity_distribution": sev_counts,
        "total_corrections_received": total_corrections,
        "false_alarm_rate": false_alarm_rate,
        "drift_indicator": drift_status,
        "drift_score": drift_score,
        "model_health": "healthy" if false_alarm_rate < 0.20 else "review_recommended",
    }


