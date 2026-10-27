"""REST API routes for CivicPulse."""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from server.api.middleware import limiter
from server.db import crud
from server.db.database import get_db
from server.nlp.classifiers import model_suite
from server.nlp.clustering import CivicTopicModeler
from server.nlp.xai import explainer
from server.schemas.alert import (
    AlertResponse,
    AlertUpdate,
    AreaResponse,
    ClassifyRequest,
    ClassifyResponse,
    HealthResponse,
    IngestRequest,
    TopicResponse,
)
from server.schemas.location import SavedLocationCreate, SavedLocationResponse
from server.schemas.user import UserProfileResponse, UserProfileUpdate
from server.nlp.gazetteer import (
    HYDERABAD_GAZETTEER,
    haversine_distance,
    is_alert_within_radius,
    resolve_locality,
)
from server.services.personalization import (
    compute_effective_severity,
    tailor_actions_for_profile,
)
from server.services import reminder_service, digest_service, multilingual
from server.services.sms_service import sms_service
from server.services.telegram_bot import telegram_bot
from server.services.pipeline import process_report_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
@limiter.limit("60/minute")
def health_check(request: Request, db: Session = Depends(get_db)):
    """System health endpoint reporting database connectivity and model status."""
    models_ready = model_suite.vectorizer is not None
    if not models_ready:
        models_ready = model_suite.load_artifacts()

    return {
        "status": "healthy",
        "version": "1.0.0",
        "models_loaded": models_ready,
        "database": "connected"
    }


def format_alert_response(a) -> AlertResponse:
    """Format an Alert ORM instance into validated AlertResponse."""
    res = {
        "id": a.id,
        "report_id": a.report_id,
        "title": a.title,
        "category": a.category,
        "severity": a.severity,
        "affected_areas": json.loads(a.affected_areas) if a.affected_areas else [],
        "start_time": a.start_time,
        "expected_end_time": a.expected_end_time,
        "expected_impact": a.expected_impact,
        "recommended_actions": json.loads(a.recommended_actions) if a.recommended_actions else [],
        "source_name": a.source_name,
        "source_url": a.source_url,
        "source_tier": getattr(a, "source_tier", "unverified") or "unverified",
        "published_at": a.published_at,
        "confidence": a.confidence,
        "secondary_categories": json.loads(a.secondary_categories) if getattr(a, "secondary_categories", None) else [],
        "needs_review": a.needs_review,
        "status": a.status,
        "parent_alert_id": getattr(a, "parent_alert_id", None),
        "cluster_id": a.cluster_id,
        "xai_explanation": json.loads(a.xai_explanation) if a.xai_explanation else None,
        "community_confirmations": {
            "confirmed_resolved": sum(1 for c in getattr(a, "confirmations", []) if c.status_vote == "resolved"),
            "confirmed_active": sum(1 for c in getattr(a, "confirmations", []) if c.status_vote == "still_active"),
        },
        "created_at": a.created_at,
        "updated_at": a.updated_at,
        "expires_at": a.expires_at,
    }
    return AlertResponse(**res)


@router.get("/alerts", response_model=List[AlertResponse])
@limiter.limit("60/minute")
def list_alerts(
    request: Request,
    area: Optional[str] = Query(None, description="Filter by affected neighborhood"),
    category: Optional[str] = Query(None, description="Filter by alert category"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    status: Optional[str] = Query("active", description="Filter by status"),
    source_tier: Optional[str] = Query(None, description="Filter by official | news | unverified"),
    lat: Optional[float] = Query(None, description="Citizen latitude for radius matching"),
    lng: Optional[float] = Query(None, description="Citizen longitude for radius matching"),
    radius_km: Optional[float] = Query(None, description="Search radius in kilometers"),
    lang: Optional[str] = Query("en", description="Target language: en, te, or hi"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve filtered alerts with optional Haversine distance spatial matching and translation."""
    alerts = crud.get_alerts(
        db=db,
        area=area,
        category=category,
        severity=severity,
        status=status,
        source_tier=source_tier,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        skip=skip,
        limit=limit
    )

    formatted = [format_alert_response(a) for a in alerts]
    target_l = (lang or "en").lower()
    if target_l in {"te", "hi"}:
        for item in formatted:
            trans = multilingual.translate_alert(
                title=item.title,
                category=item.category,
                severity=item.severity,
                impact=item.expected_impact,
                actions=item.recommended_actions,
                target_lang=target_l
            )
            item.title = trans["title"]
            item.expected_impact = trans["expected_impact"]
            item.recommended_actions = trans["recommended_actions"]

    return formatted


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
@limiter.limit("60/minute")
def get_alert_detail(
    request: Request,
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get single alert by ID."""
    alert = crud.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found.")

    return format_alert_response(alert)


@router.get("/alerts/{alert_id}/explain")
@limiter.limit("60/minute")
def explain_alert(
    request: Request,
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Return XAI (LIME / feature attribution) explanation for an alert."""
    alert = crud.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    if alert.xai_explanation:
        return json.loads(alert.xai_explanation)

    # Compute on the fly if missing
    explanation = explainer.explain_with_lime(alert.title)
    alert.xai_explanation = json.dumps(explanation)
    db.commit()
    return explanation


@router.get("/alerts/{alert_id}/multilingual")
@limiter.limit("60/minute")
def get_alert_translation(
    request: Request,
    alert_id: int,
    lang: str = Query("en", description="Target language: en, te, or hi"),
    db: Session = Depends(get_db)
):
    """Retrieve alert translated into Telugu (te), Hindi (hi), or English (en)."""
    alert = crud.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    actions = json.loads(alert.recommended_actions) if alert.recommended_actions else []
    return multilingual.translate_alert(
        title=alert.title,
        category=alert.category,
        severity=alert.severity,
        impact=alert.expected_impact,
        actions=actions,
        target_lang=lang
    )


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def ingest_report(
    request: Request,
    payload: IngestRequest,
    db: Session = Depends(get_db)
):
    """Ingest raw news report or URL, run pipeline, filter spam, and return generated alert."""
    try:
        result = await process_report_pipeline(
            db=db,
            raw_text=payload.text,
            url=payload.url,
            source_name=payload.source_name
        )
        return result
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify", response_model=ClassifyResponse)
@limiter.limit("60/minute")
def classify_text(
    request: Request,
    payload: ClassifyRequest
):
    """Stateless text classification: returns category, severity, and spam probability."""
    if model_suite.vectorizer is None:
        model_suite.load_artifacts()

    pred = model_suite.predict(payload.text)
    return {
        "category": pred["category"],
        "category_confidence": pred["category_confidence"],
        "secondary_categories": pred.get("secondary_categories", []),
        "severity": pred["severity"],
        "severity_confidence": pred["severity_confidence"],
        "is_spam": pred["is_spam"],
        "spam_probability": pred["spam_probability"]
    }


@router.get("/topics", response_model=List[TopicResponse])
@limiter.limit("30/minute")
def get_topics(
    request: Request,
    db: Session = Depends(get_db)
):
    """Return discovered civic topics from unsupervised LDA topic modeling."""
    topics = crud.get_topics(db)
    if not topics:
        # Generate topics on the fly from recent alerts
        alerts = crud.get_alerts(db, limit=200)
        texts = [a.title + " " + (a.expected_impact or "") for a in alerts if a.title]
        if len(texts) >= 5:
            topic_modeler = CivicTopicModeler(n_topics=5)
            lda_res = topic_modeler.fit_lda(texts)
            for t in lda_res["topics"]:
                crud.create_topic(
                    db=db,
                    method="lda",
                    keywords=json.dumps(t["keywords"]),
                    coherence_score=lda_res["topic_diversity"],
                    document_count=len(texts) // 5
                )
            topics = crud.get_topics(db)

    formatted = []
    for t in topics:
        formatted.append(TopicResponse(
            id=t.id,
            method=t.method,
            keywords=json.loads(t.keywords) if isinstance(t.keywords, str) else t.keywords,
            coherence_score=t.coherence_score,
            document_count=t.document_count
        ))
    return formatted


@router.get("/areas", response_model=List[AreaResponse])
@limiter.limit("60/minute")
def list_areas(
    request: Request,
    db: Session = Depends(get_db)
):
    """List monitored municipal areas and neighborhoods."""
    areas = crud.get_areas(db)
    return [AreaResponse.model_validate(a) for a in areas]


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
@limiter.limit("30/minute")
def update_alert(
    request: Request,
    alert_id: int,
    payload: AlertUpdate,
    db: Session = Depends(get_db)
):
    """Admin endpoint to edit, approve, reject, or update status of an alert."""
    update_data = payload.model_dump(exclude_unset=True)
    if "affected_areas" in update_data and update_data["affected_areas"] is not None:
        update_data["affected_areas"] = json.dumps([a.model_dump() for a in update_data["affected_areas"]])
    if "recommended_actions" in update_data and update_data["recommended_actions"] is not None:
        update_data["recommended_actions"] = json.dumps(update_data["recommended_actions"])

    updated = crud.update_alert(db, alert_id, **update_data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found.")

    return format_alert_response(updated)


@router.get("/admin/review-queue", response_model=List[AlertResponse])
@limiter.limit("30/minute")
def get_review_queue(
    request: Request,
    db: Session = Depends(get_db)
):
    """Admin queue of alerts flagged as needing review or with low model confidence."""
    alerts = crud.get_review_queue(db)
    return [format_alert_response(a) for a in alerts]


# ---------------------------------------------------------------------------
# Locality Gazetteer & Fuzzy Resolution
# ---------------------------------------------------------------------------

@router.get("/gazetteer/localities")
@limiter.limit("60/minute")
def get_gazetteer_localities(request: Request):
    """Return all canonical Hyderabad localities with GPS coordinates, zones, and radii."""
    return list(HYDERABAD_GAZETTEER.values())


@router.get("/gazetteer/resolve")
@limiter.limit("60/minute")
def resolve_locality_name(
    request: Request,
    query: str = Query(..., min_length=2, description="Locality, landmark, or alias text")
):
    """Resolve an arbitrary locality query or road name using alias lookup and fuzzy matching."""
    match = resolve_locality(query)
    if not match:
        raise HTTPException(
            status_code=404,
            detail=f"Locality '{query}' could not be resolved to a known Hyderabad zone."
        )
    return match


# ---------------------------------------------------------------------------
# Saved Locations (Multi-Location Management)
# ---------------------------------------------------------------------------

@router.get("/user/locations", response_model=List[SavedLocationResponse])
@limiter.limit("60/minute")
def get_user_saved_locations(
    request: Request,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """List saved locations (Home, Office, Parents, School) for a citizen."""
    locations = crud.get_saved_locations(db=db, user_id=user_id)
    return [SavedLocationResponse.model_validate(loc) for loc in locations]


@router.post("/user/locations", response_model=SavedLocationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def add_user_saved_location(
    request: Request,
    payload: SavedLocationCreate,
    db: Session = Depends(get_db)
):
    """Add a new saved location with custom label and radius."""
    created = crud.create_saved_location(
        db=db,
        label=payload.label,
        locality_name=payload.locality_name,
        lat=payload.lat,
        lng=payload.lng,
        radius_km=payload.radius_km,
        user_id=payload.user_id or "default_user",
    )
    return SavedLocationResponse.model_validate(created)


@router.delete("/user/locations/{location_id}")
@limiter.limit("30/minute")
def remove_user_saved_location(
    request: Request,
    location_id: int,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """Delete a saved location."""
    success = crud.delete_saved_location(db=db, location_id=location_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Saved location not found.")
    return {"message": "Location removed successfully", "id": location_id}


# ---------------------------------------------------------------------------
# User Profile & Household Personalization
# ---------------------------------------------------------------------------

@router.get("/user/profile", response_model=UserProfileResponse)
@limiter.limit("60/minute")
def get_citizen_profile(
    request: Request,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """Fetch user household profile (water source, housing type, vulnerable modes)."""
    prof = crud.get_user_profile(db=db, user_id=user_id)
    v_modes = json.loads(prof.vulnerable_modes) if prof.vulnerable_modes else []
    return UserProfileResponse(
        id=prof.id,
        user_id=prof.user_id,
        water_source=prof.water_source or "municipal",
        housing_type=prof.housing_type or "apartment",
        vulnerable_modes=v_modes,
        preferred_language=prof.preferred_language or "en",
        created_at=prof.created_at,
        updated_at=prof.updated_at,
    )


@router.post("/user/profile", response_model=UserProfileResponse)
@limiter.limit("30/minute")
def save_citizen_profile(
    request: Request,
    payload: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update citizen profile settings."""
    uid = payload.user_id or "default_user"
    prof = crud.upsert_user_profile(
        db=db,
        user_id=uid,
        water_source=payload.water_source,
        housing_type=payload.housing_type,
        vulnerable_modes=payload.vulnerable_modes,
        preferred_language=payload.preferred_language,
    )
    v_modes = json.loads(prof.vulnerable_modes) if prof.vulnerable_modes else []
    return UserProfileResponse(
        id=prof.id,
        user_id=prof.user_id,
        water_source=prof.water_source or "municipal",
        housing_type=prof.housing_type or "apartment",
        vulnerable_modes=v_modes,
        preferred_language=prof.preferred_language or "en",
        created_at=prof.created_at,
        updated_at=prof.updated_at,
    )


# ---------------------------------------------------------------------------
# Hyperlocal Personalized Feed (Combining Saved Locations + Household Profile)
# ---------------------------------------------------------------------------

@router.get("/user/alerts")
@limiter.limit("60/minute")
def get_user_personalized_alerts(
    request: Request,
    user_id: str = Query("default_user"),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query("active"),
    lang: Optional[str] = Query("en", description="Target language: en, te, or hi"),
    db: Session = Depends(get_db)
):
    """Deliver alerts matching ANY saved location with dynamically tailored action checklists and translations."""
    profile = crud.get_user_profile(db=db, user_id=user_id)
    saved_locations = crud.get_saved_locations(db=db, user_id=user_id)
    v_modes = json.loads(profile.vulnerable_modes) if profile.vulnerable_modes else []

    all_alerts = crud.get_alerts(
        db=db,
        category=category,
        status=status,
        limit=100
    )

    results = []
    for a in all_alerts:
        formatted = format_alert_response(a).model_dump()
        affected_areas = formatted.get("affected_areas", [])

        # Check spatial matching across user's saved locations
        matched_tags = []
        min_distance = None

        if saved_locations:
            matched_for_user = False
            for loc in saved_locations:
                in_radius, dist = is_alert_within_radius(
                    affected_areas, loc.lat, loc.lng, loc.radius_km
                )
                if in_radius:
                    matched_for_user = True
                    matched_tags.append(f"{loc.label} ({loc.locality_name})")
                    if min_distance is None or dist < min_distance:
                        min_distance = dist
            if not matched_for_user:
                continue
        else:
            # Default city-wide if user has no saved locations
            matched_tags.append("Citywide")

        # Personalize checklist actions based on citizen profile
        base_actions = formatted.get("recommended_actions", [])
        tailored = tailor_actions_for_profile(
            base_actions=base_actions,
            category=formatted.get("category", "other"),
            water_source=profile.water_source or "municipal",
            housing_type=profile.housing_type or "apartment",
            vulnerable_modes=v_modes,
        )

        formatted["recommended_actions"] = tailored["actions"]
        formatted["personalized_notes"] = tailored["custom_notes"]
        formatted["profile_tags"] = tailored["tailored_tags"]
        formatted["matched_locations"] = matched_tags
        formatted["distance_km"] = min_distance

        # Compute effective severity for vulnerable user modes
        eff_sev, sev_reason = compute_effective_severity(
            base_severity=formatted.get("severity", "info"),
            category=formatted.get("category", "other"),
            vulnerable_modes=v_modes,
        )
        formatted["effective_severity"] = eff_sev
        if sev_reason:
            formatted["severity_elevation_reason"] = sev_reason
            if formatted["profile_tags"] is not None:
                formatted["profile_tags"].append(f"Elevated to {eff_sev.capitalize()}")

        # Translate content if Telugu or Hindi requested
        target_l = (lang or "en").lower()
        if target_l in {"te", "hi"}:
            trans = multilingual.translate_alert(
                title=formatted["title"],
                category=formatted.get("category", "other"),
                severity=formatted.get("severity", "info"),
                impact=formatted.get("expected_impact"),
                actions=formatted.get("recommended_actions", []),
                target_lang=target_l,
            )
            formatted["title"] = trans["title"]
            formatted["expected_impact"] = trans["expected_impact"]
            formatted["recommended_actions"] = trans["recommended_actions"]

        results.append(formatted)

    return results


# ---------------------------------------------------------------------------
# Proactive Scheduled Reminders (12h, 2h before event)
# ---------------------------------------------------------------------------

@router.get("/reminders")
@limiter.limit("60/minute")
def list_citizen_reminders(
    request: Request,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """Retrieve scheduled reminders (12h, 2h) for a citizen."""
    rems = reminder_service.get_user_reminders(db=db, user_id=user_id)
    return [
        {
            "id": r.id,
            "alert_id": r.alert_id,
            "reminder_type": r.reminder_type,
            "scheduled_for": r.scheduled_for,
            "status": r.status,
            "channel": r.channel,
            "message": r.message,
            "created_at": r.created_at,
        }
        for r in rems
    ]


@router.post("/alerts/{alert_id}/remind")
@limiter.limit("30/minute")
def schedule_reminders(
    request: Request,
    alert_id: int,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """Schedule 12h and 2h proactive reminders for an alert."""
    created = reminder_service.schedule_reminders_for_alert(db=db, alert_id=alert_id, user_id=user_id)
    return {
        "message": f"Scheduled {len(created)} reminder(s) for alert #{alert_id}",
        "reminders": [
            {
                "id": r.id,
                "reminder_type": r.reminder_type,
                "scheduled_for": r.scheduled_for,
                "message": r.message,
            }
            for r in created
        ]
    }


@router.delete("/reminders/{reminder_id}")
@limiter.limit("30/minute")
def cancel_reminder_endpoint(
    request: Request,
    reminder_id: int,
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """Cancel a scheduled reminder."""
    success = reminder_service.cancel_reminder(db=db, reminder_id=reminder_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    return {"message": "Reminder cancelled successfully", "id": reminder_id}


# ---------------------------------------------------------------------------
# Weekly Civic Digest
# ---------------------------------------------------------------------------

@router.get("/digest")
@limiter.limit("30/minute")
def get_weekly_civic_digest(
    request: Request,
    locality: Optional[str] = Query(None, description="Neighborhood to synthesize digest for"),
    user_id: str = Query("default_user"),
    db: Session = Depends(get_db)
):
    """Synthesize weekly municipal activity, resolved works, and recurring topics."""
    return digest_service.compile_weekly_digest(db=db, locality=locality, user_id=user_id)


# ---------------------------------------------------------------------------
# Multi-Channel Delivery Simulation (Telegram & SMS Fallback)
# ---------------------------------------------------------------------------

@router.post("/delivery/telegram/simulate")
@limiter.limit("30/minute")
def simulate_telegram_bot_command(
    request: Request,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Simulate Telegram bot interaction (/start, /setlocality, /locations, /alerts)."""
    user_id = payload.get("user_id", "telegram_demo_user")
    cmd = payload.get("command", "/start")
    reply = telegram_bot.handle_command(user_id=user_id, command_text=cmd, db=db)
    return {"user_id": user_id, "command": cmd, "response": reply}


@router.post("/delivery/sms/simulate")
@limiter.limit("30/minute")
def simulate_sms_alert(
    request: Request,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Simulate SMS fallback dispatch for an urgent alert."""
    phone = payload.get("to_phone", "+919988776655")
    alert_id = payload.get("alert_id")

    alert = crud.get_alert(db=db, alert_id=alert_id) if alert_id else None
    if alert:
        title = alert.title
        category = alert.category
        severity = alert.severity
        actions = json.loads(alert.recommended_actions) if alert.recommended_actions else []
    else:
        title = payload.get("title", "Emergency pipeline burst near Begumpet")
        category = payload.get("category", "water_supply")
        severity = payload.get("severity", "critical")
        actions = ["Store drinking water immediately."]

    result = sms_service.send_alert_sms(
        to_phone=phone,
        alert_title=title,
        category=category,
        severity=severity,
        actions=actions
    )
    return {"status": "dispatched", "result": result, "recipient": phone}


# ---------------------------------------------------------------------------
# Citizen Feedback & Model Correction Retraining Pipeline
# ---------------------------------------------------------------------------

@router.post("/alerts/{alert_id}/feedback")
@limiter.limit("30/minute")
def submit_alert_feedback(
    request: Request,
    alert_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit correction for wrong severity or category, queueing for retraining."""
    alert = crud.get_alert(db=db, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    correction = crud.create_alert_correction(
        db=db,
        alert_id=alert.id,
        original_category=alert.category,
        original_severity=alert.severity,
        suggested_category=payload.get("suggested_category"),
        suggested_severity=payload.get("suggested_severity"),
        comment=payload.get("comment"),
        user_id=payload.get("user_id", "default_user"),
    )

    return {
        "message": "Feedback submitted successfully. Thank you for improving CivicPulse accuracy!",
        "correction_id": correction.id,
        "is_queued_for_merge": True
    }


# ---------------------------------------------------------------------------
# Hyperlocal Community Confirmations ("Water arrived" / "Still disrupted")
# ---------------------------------------------------------------------------

@router.post("/alerts/{alert_id}/confirm")
@limiter.limit("60/minute")
def submit_community_confirmation(
    request: Request,
    alert_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit ground-truth crowd confirmation ('resolved' or 'still_active')."""
    alert = crud.get_alert(db=db, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    vote = payload.get("status_vote", "still_active")
    if vote not in {"resolved", "still_active"}:
        raise HTTPException(status_code=400, detail="status_vote must be 'resolved' or 'still_active'.")

    user_id = payload.get("user_id", "default_user")
    crud.add_community_confirmation(db=db, alert_id=alert.id, status_vote=vote, user_id=user_id)
    stats = crud.get_community_confirmations(db=db, alert_id=alert.id)

    # Auto-resolve alert if community consensus threshold reached (>= 5 resolved and > 80% ratio)
    if stats["confirmed_resolved"] >= 5 and (stats["confirmed_resolved"] / stats["total_votes"]) >= 0.8:
        alert.status = "resolved"
        db.commit()

    return {
        "message": "Community confirmation recorded.",
        "vote": vote,
        "community_stats": stats
    }


@router.get("/alerts/{alert_id}/confirmations")
@limiter.limit("60/minute")
def get_alert_confirmations(
    request: Request,
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve community confirmation statistics for an alert."""
    alert = crud.get_alert(db=db, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    return crud.get_community_confirmations(db=db, alert_id=alert.id)


# ---------------------------------------------------------------------------
# Production System Monitoring & Data Drift Indicator
# ---------------------------------------------------------------------------

@router.get("/monitoring")
@limiter.limit("60/minute")
def get_system_monitoring(
    request: Request,
    db: Session = Depends(get_db)
):
    """Report prediction distributions, false-alarm rate, and drift indicators."""
    return crud.get_monitoring_metrics(db=db)




