"""
SQLAlchemy ORM models for CivicPulse.

All JSON-serialised fields (``affected_areas``, ``recommended_actions``,
``keywords``, ``xai_explanation``) are stored as ``Text`` columns and must
be serialised / deserialised by the application layer (see ``server.schemas``).
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from server.db.database import Base


def _utcnow() -> datetime:
    """Return the current UTC timestamp (timezone-aware)."""
    return datetime.now(timezone.utc)


class Report(Base):
    """Raw text report ingested from an RSS feed, URL scrape, or manual entry."""

    __tablename__ = "reports"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    raw_text: str = Column(Text, nullable=False)
    source_url: str | None = Column(String(2048), nullable=True)
    source_name: str | None = Column(String(200), nullable=True)
    source_type: str = Column(String(20), default="manual")  # rss | manual | url
    ingested_at: datetime = Column(DateTime, default=_utcnow)
    is_spam: bool = Column(Boolean, default=False)
    spam_probability: float = Column(Float, default=0.0)


class Alert(Base):
    """Processed civic alert derived from one or more reports."""

    __tablename__ = "alerts"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    report_id: int | None = Column(Integer, ForeignKey("reports.id"), nullable=True)

    title: str = Column(String(500), nullable=False)
    category: str = Column(String(50), nullable=False)
    # road_closure | water_supply | power_cut | severe_weather | public_service | other
    secondary_categories: str | None = Column(Text, nullable=True)  # JSON list of strings (e.g. ["severe_weather"])
    severity: str = Column(String(20), nullable=False)
    # info | advisory | warning | critical

    affected_areas: str | None = Column(Text, nullable=True)  # JSON list of {name, lat, lng}
    start_time: datetime | None = Column(DateTime, nullable=True)
    expected_end_time: datetime | None = Column(DateTime, nullable=True)
    expected_impact: str | None = Column(Text, nullable=True)
    recommended_actions: str | None = Column(Text, nullable=True)  # JSON list of strings

    source_name: str | None = Column(String(200), nullable=True)
    source_url: str | None = Column(String(2048), nullable=True)
    published_at: datetime | None = Column(DateTime, nullable=True)
    source_tier: str = Column(String(20), default="unverified")
    # official | news | unverified

    confidence: float = Column(Float, default=0.5)
    needs_review: bool = Column(Boolean, default=True)
    status: str = Column(String(20), default="active")
    # active | updated | cancelled | resolved | past | rejected

    parent_alert_id: int | None = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    xai_explanation: str | None = Column(Text, nullable=True)  # SHAP/LIME data (JSON)
    cluster_id: int | None = Column(Integer, nullable=True)
    preprocessed_text: str | None = Column(Text, nullable=True)

    created_at: datetime = Column(DateTime, default=_utcnow)
    updated_at: datetime = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    expires_at: datetime | None = Column(DateTime, nullable=True)

    # Relationships
    report = relationship("Report", backref="alerts")
    parent_alert = relationship("Alert", remote_side=[id], backref="child_updates")


class Topic(Base):
    """Topic cluster produced by LDA or K-Means."""

    __tablename__ = "topics"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    method: str = Column(String(20))  # lda | kmeans
    keywords: str | None = Column(Text, nullable=True)  # JSON – top-10 words
    coherence_score: float | None = Column(Float, nullable=True)
    document_count: int = Column(Integer, default=0)
    created_at: datetime = Column(DateTime, default=_utcnow)


class Area(Base):
    """Geographic area referenced by alerts."""

    __tablename__ = "areas"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(200), unique=True, nullable=False)
    city: str = Column(String(100), nullable=False)
    lat: float | None = Column(Float, nullable=True)
    lng: float | None = Column(Float, nullable=True)


class SavedLocation(Base):
    """User-saved named locations (e.g. Home, Office, Parents, School) for hyperlocal alerts."""

    __tablename__ = "saved_locations"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: str = Column(String(100), default="default_user", index=True, nullable=False)
    label: str = Column(String(100), nullable=False)  # "Home" | "Office" | "Parents" | "School" | custom
    locality_name: str = Column(String(200), nullable=False)
    lat: float = Column(Float, nullable=False)
    lng: float = Column(Float, nullable=False)
    radius_km: float = Column(Float, default=5.0)
    created_at: datetime = Column(DateTime, default=_utcnow)


class UserProfile(Base):
    """Personalized profile settings (water source, housing type, vulnerable modes)."""

    __tablename__ = "user_profiles"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: str = Column(String(100), unique=True, index=True, nullable=False)
    water_source: str = Column(String(50), default="municipal")  # municipal | borewell | tanker | mixed
    housing_type: str = Column(String(50), default="apartment")  # apartment | independent | villa
    vulnerable_modes: str | None = Column(Text, nullable=True)  # JSON list: ["elderly", "wfh", "dialysis", "home_oxygen"]
    preferred_language: str = Column(String(10), default="en")  # en | te | hi
    created_at: datetime = Column(DateTime, default=_utcnow)
    updated_at: datetime = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class AlertReminder(Base):
    """Scheduled citizen reminder for upcoming civic disruptions (12h, 2h before)."""

    __tablename__ = "alert_reminders"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    alert_id: int = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    user_id: str = Column(String(100), default="default_user", index=True, nullable=False)
    reminder_type: str = Column(String(20), default="2h")  # 12h | 2h | immediate
    scheduled_for: datetime = Column(DateTime, nullable=False)
    status: str = Column(String(20), default="scheduled")  # scheduled | delivered | cancelled
    channel: str = Column(String(20), default="in_app")  # in_app | telegram | sms
    message: str = Column(Text, nullable=False)
    created_at: datetime = Column(DateTime, default=_utcnow)

    # Relationships
    alert = relationship("Alert", backref="reminders")


class AlertCorrection(Base):
    """Citizen feedback correcting model category or severity predictions."""

    __tablename__ = "alert_corrections"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    alert_id: int = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    user_id: str = Column(String(100), default="default_user", nullable=False)
    original_category: str = Column(String(50), nullable=False)
    suggested_category: str | None = Column(String(50), nullable=True)
    original_severity: str = Column(String(20), nullable=False)
    suggested_severity: str | None = Column(String(20), nullable=True)
    comment: str | None = Column(Text, nullable=True)
    is_merged: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime, default=_utcnow)

    alert = relationship("Alert", backref="corrections")


class CommunityConfirmation(Base):
    """Hyperlocal crowd verification votes (e.g. 'Water arrived' vs 'Still disrupted')."""

    __tablename__ = "community_confirmations"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    alert_id: int = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    user_id: str = Column(String(100), default="default_user", nullable=False)
    status_vote: str = Column(String(30), nullable=False)  # "resolved" | "still_active"
    created_at: datetime = Column(DateTime, default=_utcnow)

    alert = relationship("Alert", backref="confirmations")



