"""End-to-End Civic Alert Processing Pipeline for CivicPulse.

Orchestrates:
1. Ingestion (Text / URL)
2. Configurable text preprocessing
3. Binary spam detection (filters ads/clickbait before they become alerts)
4. Alert category classification (6 classes)
5. Severity / Urgency classification (4 levels)
6. spaCy NER baseline location extraction
7. Gemini LLM structured field extraction (with Pydantic validation)
8. XAI feature attribution (LIME / SHAP explanations)
9. Deduplication clustering
10. Database persistence via SQLAlchemy
"""

import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from server.db import crud
from server.nlp.classifiers import model_suite
from server.nlp.ner import extract_entities_spacy
from server.nlp.preprocess import default_preprocessor
from server.nlp.xai import explainer
from server.services.gemini_service import gemini_service
from server.services.rss_service import rss_service

logger = logging.getLogger(__name__)

OFFICIAL_SOURCES = {
    "ghmc", "hmwssb", "tgspdcl", "tsspdcl", "hyderabad traffic police", "hydtp",
    "imd", "government of telangana", "telangana govt", "municipal corporation",
    "disaster response", "traffic police", "police department", "fire and rescue services",
    "fire and rescue", "state electricity board", "state meteorological dept", 
    "tgspdcl southern power", "water supply", "sewerage board", "district collectorate", 
    "public transport", "collectorate", "transport corporation", "tsrtc", "rtc"
}

NEWS_SOURCES = {
    "times of india", "the hindu", "deccan chronicle", "telangana today", "ndtv",
    "indian express", "metro mirror", "deccan herald", "hindustan times", "news18",
    "city express", "journal", "civic watch", "daily news", "herald", "express", "mirror"
}

CANCELLATION_PHRASES = [
    "cancelled", "canceled", "restored", "cleared", "resumed",
    "withdrawn", "lifted", "called off", "resolved", "back to normal"
]

UPDATE_PHRASES = [
    "postponed", "rescheduled", "deferred", "delayed", "revised", "extended"
]


def resolve_source_tier(source_name: Optional[str], raw_text: str) -> str:
    """Classify source credibility tier: official, news, or unverified."""
    s_name = (source_name or "").lower().strip()
    text_prefix = raw_text.lower()[:120]

    for off in OFFICIAL_SOURCES:
        if off in s_name or off in text_prefix:
            return "official"

    for news in NEWS_SOURCES:
        if news in s_name:
            return "news"

    return "unverified"


def detect_status_and_event_link(
    raw_text: str,
    affected_areas: list,
    category: str,
    db: Session
) -> tuple[str, Optional[int]]:
    """Detect if report updates/cancels a prior alert and mark stale alert resolved."""
    lower_text = raw_text.lower()

    is_cancelled = any(phrase in lower_text for phrase in CANCELLATION_PHRASES)
    is_updated = any(phrase in lower_text for phrase in UPDATE_PHRASES)

    if not is_cancelled and not is_updated:
        return "active", None

    target_status = "resolved" if is_cancelled else "updated"

    # Search existing alerts in database with overlapping locality & category
    area_names = [a.get("name", "").lower() for a in affected_areas if isinstance(a, dict) and a.get("name")]
    if not area_names:
        area_names = ["hyderabad"]

    from server.db.models import Alert
    candidates = (
        db.query(Alert)
        .filter(Alert.category == category)
        .filter(Alert.status.in_(["active", "upcoming", "updated"]))
        .order_by(Alert.created_at.desc())
        .limit(20)
        .all()
    )

    matched_parent_id = None
    for cand in candidates:
        cand_areas = cand.affected_areas.lower() if cand.affected_areas else ""
        if any(an in cand_areas for an in area_names):
            matched_parent_id = cand.id
            cand.status = target_status
            cand.needs_review = False
            db.commit()
            logger.info(f"Linked new alert to prior Alert #{cand.id}, updating status to '{target_status}'.")
            break

    return target_status, matched_parent_id


def check_duplicate_alert(
    raw_text: str,
    cleaned_text: str,
    predicted_category: str,
    source_url: Optional[str],
    db: Session,
    similarity_threshold: float = 0.58
) -> Optional[Any]:
    """Check if an active alert already exists that duplicates this incoming report.

    Checks:
    1. Exact source URL match against active/upcoming alerts.
    2. Exact preprocessed text match against active/upcoming alerts.
    3. TF-IDF cosine similarity against recent alerts in the same category or overall.
    """
    from server.db.models import Alert
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    # 1. Exact Source URL match
    if source_url and len(source_url.strip()) > 5:
        existing_url = (
            db.query(Alert)
            .filter(Alert.source_url == source_url.strip())
            .filter(Alert.status.in_(["active", "upcoming", "updated"]))
            .order_by(Alert.created_at.desc())
            .first()
        )
        if existing_url:
            logger.info(f"Duplicate found by exact source URL match: Alert #{existing_url.id}")
            return existing_url

    # Query active candidate alerts
    candidates = (
        db.query(Alert)
        .filter(Alert.status.in_(["active", "upcoming", "updated"]))
        .order_by(Alert.created_at.desc())
        .limit(60)
        .all()
    )
    if not candidates:
        return None

    # 2. Exact or near-exact normalized text match
    norm_in = cleaned_text.strip().lower()
    raw_in = raw_text.strip().lower()
    for cand in candidates:
        cand_clean = (cand.preprocessed_text or "").strip().lower()
        if cand_clean and (cand_clean == norm_in or norm_in in cand_clean or cand_clean in norm_in):
            logger.info(f"Duplicate found by exact preprocessed text match: Alert #{cand.id}")
            return cand

    # 3. TF-IDF Cosine Similarity
    candidate_texts = []
    valid_candidates = []
    for cand in candidates:
        c_text = cand.preprocessed_text or f"{cand.title} {cand.expected_impact or ''}"
        if cand.report and cand.report.raw_text:
            c_text = cand.report.raw_text
        if len(c_text.strip()) > 10:
            candidate_texts.append(default_preprocessor.preprocess(c_text))
            valid_candidates.append(cand)

    if not candidate_texts:
        return None

    try:
        tfidf = TfidfVectorizer(max_features=2500, stop_words="english")
        norm_incoming = default_preprocessor.preprocess(cleaned_text or raw_text)
        all_texts = [norm_incoming] + candidate_texts
        X = tfidf.fit_transform(all_texts)
        sims = cosine_similarity(X[0:1], X[1:])[0]

        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])
        best_cand = valid_candidates[best_idx]

        # If categories match, use similarity_threshold (0.58).
        # If categories differ, require high similarity (0.80) to avoid false positives.
        effective_threshold = similarity_threshold if best_cand.category == predicted_category else 0.80

        if best_sim >= effective_threshold:
            logger.info(
                f"Duplicate found by cosine similarity ({best_sim:.2f} >= {effective_threshold:.2f}): "
                f"Matches Alert #{best_cand.id} ('{best_cand.title}')"
            )
            return best_cand
    except Exception as e:
        logger.warning(f"Error during duplicate similarity check: {e}")

    return None


async def process_report_pipeline(
    db: Session,
    raw_text: Optional[str] = None,
    url: Optional[str] = None,
    source_name: Optional[str] = None
) -> Dict[str, Any]:
    """Execute the full CivicPulse intelligent pipeline."""
    # Ensure models are loaded
    if model_suite.vectorizer is None:
        model_suite.load_artifacts()

    # Step 1: Scrape if URL provided
    source_url = url
    if url and not raw_text:
        scraped = await rss_service.fetch_article_text(url)
        if not scraped or not scraped["text"]:
            raise ValueError(f"Could not extract readable article text from {url}")
        raw_text = scraped["text"]
        source_name = source_name or scraped.get("domain", "Web Article")

    if not raw_text or len(raw_text.strip()) < 15:
        raise ValueError("Report text is too short or empty for processing.")

    # Step 2: Preprocess text
    cleaned_text = default_preprocessor.preprocess(raw_text)

    # Step 3: Spam / Irrelevant Report Filtering
    clf_res = model_suite.predict(raw_text)
    is_spam = clf_res["is_spam"]
    spam_prob = clf_res["spam_probability"]

    # Store incoming raw report in database
    report = crud.create_report(
        db=db,
        raw_text=raw_text,
        source_url=source_url,
        source_name=source_name or "Manual Report",
        source_type="url" if url else "manual",
        is_spam=is_spam,
        spam_probability=spam_prob
    )

    # If spam, filter immediately
    if is_spam:
        logger.info(f"Report #{report.id} flagged as spam ({spam_prob:.2f}). Alert not created.")
        return {
            "status": "filtered",
            "message": "Report was identified as commercial spam or irrelevant news.",
            "report_id": report.id,
            "is_spam": True,
            "spam_probability": spam_prob,
            "alert": None
        }

    # Step 4: Category and Severity Prediction
    predicted_cat = clf_res["category"]
    predicted_sev = clf_res["severity"]

    # Step 4b: Check if this report is an update or cancellation
    lower_raw = raw_text.lower()
    is_status_change = any(p in lower_raw for p in CANCELLATION_PHRASES) or any(p in lower_raw for p in UPDATE_PHRASES)

    # Step 4c: Duplicate Detection (suppress redundant alert creation if incident is already active)
    if not is_status_change:
        duplicate_cand = check_duplicate_alert(
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            predicted_category=predicted_cat,
            source_url=source_url,
            db=db
        )
        if duplicate_cand:
            logger.info(
                f"Duplicate incident detected: Report #{report.id} matches active Alert #{duplicate_cand.id} "
                f"('{duplicate_cand.title}'). Suppressing duplicate alert creation."
            )
            dup_areas = []
            if duplicate_cand.affected_areas:
                try:
                    dup_areas = json.loads(duplicate_cand.affected_areas)
                except Exception:
                    pass

            dup_alert_dict = {
                "id": duplicate_cand.id,
                "title": duplicate_cand.title,
                "category": duplicate_cand.category,
                "severity": duplicate_cand.severity,
                "affected_areas": dup_areas,
                "expected_impact": duplicate_cand.expected_impact,
                "source_name": duplicate_cand.source_name,
                "source_url": duplicate_cand.source_url,
                "source_tier": duplicate_cand.source_tier,
                "status": duplicate_cand.status,
                "confidence": duplicate_cand.confidence,
                "created_at": duplicate_cand.created_at.isoformat() if duplicate_cand.created_at else None,
            }

            return {
                "status": "duplicate",
                "message": f"Duplicate incident detected: Already active as Alert #{duplicate_cand.id} ('{duplicate_cand.title}').",
                "is_duplicate": True,
                "existing_alert_id": duplicate_cand.id,
                "report_id": report.id,
                "is_spam": False,
                "spam_probability": spam_prob,
                "alert": dup_alert_dict,
                "title": duplicate_cand.title,
                "category": duplicate_cand.category,
                "severity": duplicate_cand.severity,
                "affected_areas": dup_areas,
                "expected_impact": duplicate_cand.expected_impact,
                "source_name": duplicate_cand.source_name,
                "source_tier": duplicate_cand.source_tier,
            }

    # Step 5: spaCy NER Baseline
    spacy_ents = extract_entities_spacy(raw_text)

    # Step 6: Gemini LLM Structured Extraction (with offline fallback)
    extracted = gemini_service.extract_structured_alert(
        raw_text=raw_text,
        predicted_category=predicted_cat,
        predicted_severity=predicted_sev,
        source_name=source_name,
        source_url=source_url
    )

    # Step 7: Explainable AI (LIME explanation)
    try:
        xai_data = explainer.explain_with_lime(raw_text, num_features=6)
    except Exception as e:
        logger.warning(f"Failed to generate XAI: {e}")
        xai_data = {
            "predicted_category": predicted_cat,
            "positive_features": [],
            "negative_features": [],
            "summary": "Attribution features unavailable."
        }

    # Step 8: Source Credibility Tier & Update/Cancellation Link
    source_tier = resolve_source_tier(extracted.get("source_name", source_name), raw_text)
    alert_status, parent_alert_id = detect_status_and_event_link(
        raw_text=raw_text,
        affected_areas=extracted.get("affected_areas", []),
        category=extracted.get("category", predicted_cat),
        db=db
    )

    # Step 9: Database Alert Persistence
    alert_kwargs = {
        "report_id": report.id,
        "title": extracted.get("title", "Civic Alert"),
        "category": extracted.get("category", predicted_cat),
        "severity": extracted.get("severity", predicted_sev),
        "affected_areas": json.dumps(extracted.get("affected_areas", [])),
        "start_time": extracted.get("start_time"),
        "expected_end_time": extracted.get("expected_end_time"),
        "expected_impact": extracted.get("expected_impact"),
        "recommended_actions": json.dumps(extracted.get("recommended_actions", [])),
        "source_name": extracted.get("source_name", source_name),
        "source_url": extracted.get("source_url", source_url),
        "source_tier": source_tier,
        "confidence": extracted.get("confidence", clf_res["category_confidence"]),
        "secondary_categories": json.dumps(clf_res.get("secondary_categories", [])),
        "needs_review": extracted.get("needs_review", False),
        "status": alert_status,
        "parent_alert_id": parent_alert_id,
        "xai_explanation": json.dumps(xai_data),
        "preprocessed_text": cleaned_text
    }

    alert = crud.create_alert(db=db, **alert_kwargs)

    # Populate Areas table with any new areas
    for area_obj in extracted.get("affected_areas", []):
        area_name = area_obj.get("name")
        if area_name and len(area_name) > 2:
            try:
                crud.create_area(
                    db=db,
                    name=area_name,
                    city="Hyderabad",
                    lat=area_obj.get("lat"),
                    lng=area_obj.get("lng")
                )
            except Exception:
                pass  # Ignore existing duplicate area names

    logger.info(f"Created active alert #{alert.id} ({alert.category} - {alert.severity}) from report #{report.id}.")

    alert_dict = {
        "id": alert.id,
        "report_id": report.id,
        "title": alert.title,
        "category": alert.category,
        "secondary_categories": clf_res.get("secondary_categories", []),
        "severity": alert.severity,
        "source_tier": alert.source_tier,
        "status": alert.status,
        "parent_alert_id": alert.parent_alert_id,
        "affected_areas": extracted.get("affected_areas", []),
        "expected_impact": alert.expected_impact,
        "recommended_actions": extracted.get("recommended_actions", []),
        "confidence": alert.confidence,
        "source_name": alert.source_name,
        "source_url": alert.source_url,
        "start_time": alert.start_time.isoformat() if alert.start_time else None,
        "expected_end_time": alert.expected_end_time.isoformat() if alert.expected_end_time else None,
        "created_at": alert.created_at.isoformat() if alert.created_at else None
    }

    return {
        "status": "success",
        "message": "Report successfully analyzed and alert created.",
        "is_spam": False,
        "spam_probability": spam_prob,
        "report_id": report.id,
        "alert_id": alert.id,
        "title": alert.title,
        "category": alert.category,
        "secondary_categories": clf_res.get("secondary_categories", []),
        "severity": alert.severity,
        "source_tier": alert.source_tier,
        "alert_status": alert.status,
        "parent_alert_id": alert.parent_alert_id,
        "affected_areas": extracted.get("affected_areas", []),
        "expected_impact": alert.expected_impact,
        "recommended_actions": extracted.get("recommended_actions", []),
        "confidence": alert.confidence,
        "needs_review": alert.needs_review,
        "xai_explanation": xai_data,
        "alert": alert_dict
    }
