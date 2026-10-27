"""Main FastAPI application entry point for CivicPulse."""

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from server.api.middleware import limiter
from server.api.routes import router
from server.config import settings
from server.db import crud
from server.db.database import SessionLocal, init_db
from server.nlp.classifiers import model_suite

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("civicpulse")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def seed_database_if_empty():
    """Populate initial database from seed dataset if no alerts exist."""
    db = SessionLocal()
    try:
        existing = crud.get_alerts(db, limit=1)
        if not existing:
            logger.info("Database is empty. Seeding initial demo alerts from seed_data.json...")
            seed_file = PROJECT_ROOT / "seed" / "seed_data.json"
            if seed_file.exists():
                with open(seed_file, "r", encoding="utf-8") as f:
                    seed_data = json.load(f)

                # Category-specific action checklists (3 to 4 concrete actionable steps)
                CATEGORY_ACTIONS = {
                    "road_closure": [
                        "Plan an alternate detour route avoiding the impacted junction.",
                        "Expect 20–30 minutes additional commute delay during rush hours.",
                        "Follow directional signage and Hyderabad Traffic Police marshals' instructions.",
                        "Use Hyderabad Metro or public transit to bypass arterial road congestion."
                    ],
                    "water_supply": [
                        "Store at least 20–30 liters of drinking and household water in advance.",
                        "Boil municipal water for at least 3 minutes before consumption if pressure drops.",
                        "Call HMWSSB helpline (1916) or use mobile app to book priority water tankers.",
                        "Turn off booster pumps to prevent motor burnout during zero-pressure hours."
                    ],
                    "power_cut": [
                        "Keep essential medical life-support devices, UPS inverters, and phones fully charged.",
                        "Unplug sensitive electronics and air conditioners to avoid voltage surge damage.",
                        "Keep deep freezers and refrigerators closed to preserve food freshness.",
                        "Report localized feeder trips or wire hazards to TGSPDCL hotline (1912)."
                    ],
                    "severe_weather": [
                        "Stay indoors and avoid parking vehicles beneath old trees or overhead cables.",
                        "Do not drive through inundated underpasses or submerged low-lying road stretches.",
                        "Keep emergency flashlights, battery radios, and first aid kits accessible.",
                        "Monitor GHMC Disaster Response Force (DRF) real-time alerts on 040-21111111."
                    ],
                    "public_service": [
                        "Verify official counter operating hours and required documents before visiting.",
                        "Use online municipal portals (ghmc.gov.in) for non-urgent citizen grievances.",
                        "Follow on-site queue tokens and administrative guidance.",
                        "Contact the municipal citizen helpline (040-21111111) for service assistance."
                    ],
                    "public_health": [
                        "Verify dispensary/health camp operating hours and bring valid government ID.",
                        "Ensure routine prescriptions and emergency medicines are replenished in advance.",
                        "Follow sanitation protocols and vector control advisories in your neighborhood.",
                        "Contact Telangana Health Helpline (104) for medical guidance."
                    ],
                    "other": [
                        "Follow municipal advisories.",
                        "Plan alternate arrangements."
                    ]
                }

                def extract_clean_headline(raw_text: str, max_chars: int = 140) -> str:
                    cleaned = re.sub(r"\s+", " ", raw_text).strip()
                    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
                    first_sent = sentences[0].strip().rstrip(".") if sentences else cleaned
                    if len(first_sent) <= max_chars:
                        return first_sent
                    return first_sent[:max_chars].rsplit(" ", 1)[0] + "…"

                # Ensure balanced sample spanning all 5 categories
                categories_to_cover = ["water_supply", "power_cut", "road_closure", "severe_weather", "public_service"]
                balanced_items = []
                for cat in categories_to_cover:
                    cat_items = [d for d in seed_data if not d.get("is_spam", False) and d.get("category") == cat][:15]
                    balanced_items.extend(cat_items)

                if len(balanced_items) < 30:
                    balanced_items = [d for d in seed_data if not d.get("is_spam", False)][:75]

                from server.services.pipeline import resolve_source_tier
                from server.nlp.time_extractor import extract_temporal_fields

                for item in balanced_items:
                    area_name = item.get("affected_area", "Gachibowli")
                    areas = [{"name": area_name, "lat": 17.4401, "lng": 78.3489}]
                    cat = item["category"]
                    sev = item["severity"]
                    title = extract_clean_headline(item["text"])

                    # Category-specific expected impact
                    if cat == "road_closure":
                        impact = f"Traffic movement restricted around {area_name} due to municipal works or event. Diversions in effect."
                    elif cat == "water_supply":
                        impact = f"Drinking water supply suspended or low pressure across {area_name}. Tanker supplies deployed for critical needs."
                    elif cat == "power_cut":
                        impact = f"Scheduled electricity shutdown impacting residential and commercial feeders in {area_name}."
                    elif cat == "severe_weather":
                        impact = f"Extreme weather conditions forecast in {area_name}. Risk of waterlogging, strong wind gusts, and fallen branches."
                    elif cat == "public_service":
                        impact = f"Temporary modification in public utility service operations in {area_name}. Administrative counters updated."
                    elif cat == "public_health":
                        impact = f"Public health camp or municipal medical initiative active in {area_name}. Health services operating on adjusted schedules."
                    else:
                        impact = f"Civic bulletin issued for {area_name} residents."

                    actions = CATEGORY_ACTIONS.get(cat, CATEGORY_ACTIONS["other"])
                    source_tier = resolve_source_tier(item.get("source_name"), item["text"])
                    temporal = extract_temporal_fields(item["text"])

                    # Model confidence calculation
                    pred_res = model_suite.predict(item["text"]) if model_suite.vectorizer else None
                    conf = round(float(pred_res["category_confidence"]), 2) if pred_res else 0.88

                    crud.create_alert(
                        db=db,
                        title=title,
                        category=cat,
                        severity=sev,
                        affected_areas=json.dumps(areas),
                        start_time=temporal.get("start_time"),
                        expected_end_time=temporal.get("expected_end_time"),
                        expected_impact=impact,
                        recommended_actions=json.dumps(actions),
                        source_name=item.get("source_name", "Official Municipal Notice"),
                        source_url=item.get("source_url") or "https://ghmc.gov.in",
                        source_tier=source_tier,
                        confidence=conf,
                        needs_review=False,
                        status="active",
                        xai_explanation=json.dumps({
                            "predicted_category": cat,
                            "positive_features": [{"token": cat.split("_")[0], "weight": 0.25}],
                            "negative_features": [],
                            "summary": f"Classified as {cat} based on extracted civic terms."
                        })
                    )

                    # Also seed Area record
                    try:
                        crud.create_area(db=db, name=area_name, city="Hyderabad", lat=17.4401, lng=78.3489)
                    except Exception:
                        pass

                logger.info(f"Successfully seeded {len(balanced_items)} balanced initial alerts across all categories.")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: Initialize DB, train/load models, and seed demo records."""
    logger.info("CivicPulse starting up...")
    init_db()

    # Load or train ML suite
    loaded = model_suite.load_artifacts()
    if not loaded:
        logger.info("Training initial model suite on seed data...")
        seed_path = PROJECT_ROOT / "seed" / "seed_data.json"
        rep_path = PROJECT_ROOT / "reports"
        model_suite.train_suite(seed_path, reports_dir=rep_path)

    # Seed demo alerts if DB is empty
    seed_database_if_empty()
    logger.info("CivicPulse initialized and ready to serve alerts.")

    yield
    logger.info("CivicPulse shutting down...")


app = FastAPI(
    title="CivicPulse API",
    description="Intelligent NLP system transforming unstructured news into actionable civic alerts.",
    version="1.0.0",
    lifespan=lifespan
)

# SlowAPI Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(router)

# Mount static reports directory if present
reports_path = PROJECT_ROOT / "reports"
if reports_path.exists():
    app.mount("/reports", StaticFiles(directory=str(reports_path)), name="reports")


@app.get("/")
def root():
    return {
        "name": "CivicPulse API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "description": "Location-specific actionable civic alerts pipeline"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
