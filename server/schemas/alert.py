"""
Pydantic v2 request / response schemas for the CivicPulse alert API.

These models handle serialisation, validation, and OpenAPI documentation.
JSON-serialised ORM fields (``affected_areas``, ``recommended_actions``, etc.)
are automatically converted to / from their Python equivalents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class AffectedArea(BaseModel):
    """A geographic area affected by an alert."""

    name: str
    lat: float | None = None
    lng: float | None = None


# ---------------------------------------------------------------------------
# Alert schemas
# ---------------------------------------------------------------------------

class AlertBase(BaseModel):
    """Common fields shared between create and response schemas."""

    title: str = Field(..., max_length=500)
    category: Literal[
        "road_closure",
        "water_supply",
        "power_cut",
        "severe_weather",
        "public_service",
        "other",
    ]
    severity: Literal["info", "advisory", "warning", "critical"]
    affected_areas: list[AffectedArea] = []
    start_time: datetime | None = None
    expected_end_time: datetime | None = None
    expected_impact: str | None = Field(None, max_length=200)
    recommended_actions: list[str] = []
    source_name: str | None = None
    source_url: str | None = None
    source_tier: Literal["official", "news", "unverified"] = "unverified"
    published_at: datetime | None = None
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    secondary_categories: list[str] = []
    needs_review: bool = True
    parent_alert_id: int | None = None


class AlertCreate(AlertBase):
    """Schema for creating a new alert."""

    report_id: int | None = None
    status: Literal["active", "updated", "cancelled", "resolved", "past", "rejected", "upcoming"] = "active"


class AlertUpdate(BaseModel):
    """Schema for partially updating an alert (PATCH semantics)."""

    title: str | None = None
    category: Literal[
        "road_closure",
        "water_supply",
        "power_cut",
        "severe_weather",
        "public_service",
        "other",
    ] | None = None
    severity: Literal["info", "advisory", "warning", "critical"] | None = None
    status: Literal["active", "updated", "cancelled", "resolved", "past", "rejected", "upcoming"] | None = None
    source_tier: Literal["official", "news", "unverified"] | None = None
    parent_alert_id: int | None = None
    affected_areas: list[AffectedArea] | None = None
    expected_impact: str | None = None
    recommended_actions: list[str] | None = None
    secondary_categories: list[str] | None = None
    needs_review: bool | None = None
    expires_at: datetime | None = None


class AlertResponse(AlertBase):
    """Schema returned to clients after reading / creating an alert."""

    id: int
    report_id: int | None = None
    status: Literal["active", "updated", "cancelled", "resolved", "past", "rejected", "upcoming"] = "active"
    cluster_id: int | None = None
    xai_explanation: dict | None = None  # type: ignore[type-arg]
    community_confirmations: dict[str, int] | None = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Ingest / Classify
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    """Payload for the ingestion endpoint – either ``text`` or ``url`` is required."""

    text: str | None = Field(None, min_length=10)
    raw_text: str | None = None
    url: str | None = None
    source_name: str | None = None

    @model_validator(mode="after")
    def check_text_or_url(self) -> "IngestRequest":
        """Ensure at least one of ``text`` or ``url`` is provided."""
        if not self.text and self.raw_text:
            self.text = self.raw_text
        if not self.text and not self.url:
            raise ValueError("Either text or url must be provided")
        return self


class ClassifyRequest(BaseModel):
    """Payload for the text-classification endpoint."""

    text: str = Field(..., min_length=10)


class ClassifyResponse(BaseModel):
    """Classification results returned by the NLP pipeline."""

    category: str
    category_confidence: float
    secondary_categories: list[str] = []
    severity: str
    severity_confidence: float
    is_spam: bool
    spam_probability: float


# ---------------------------------------------------------------------------
# Topics & Areas
# ---------------------------------------------------------------------------

class TopicResponse(BaseModel):
    """Topic cluster information returned to clients."""

    id: int
    method: str
    keywords: list[str]
    coherence_score: float | None
    document_count: int

    model_config = ConfigDict(from_attributes=True)


class AreaResponse(BaseModel):
    """Geographic area information returned to clients."""

    id: int
    name: str
    city: str
    lat: float | None
    lng: float | None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Response for the ``/health`` endpoint."""

    status: str = "healthy"
    version: str = "1.0.0"
    models_loaded: bool
    database: str
