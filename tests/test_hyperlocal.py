"""Tests for Saved Locations, User Profile, and Personalized Action Checklists."""

import json
import pytest
from sqlalchemy.orm import Session

from server.db.database import SessionLocal, init_db
from server.db import crud
from server.schemas.location import SavedLocationCreate, SavedLocationResponse
from server.schemas.user import UserProfileBase, UserProfileResponse
from server.services.personalization import tailor_actions_for_profile


@pytest.fixture
def db_session():
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_personalization_water_supply():
    """Verify water supply checklist adapts to borewell, tanker, and housing type."""
    base_actions = ["Store sufficient drinking water in advance."]

    # Borewell + Apartment
    res_borewell = tailor_actions_for_profile(
        base_actions=base_actions,
        category="water_supply",
        water_source="borewell",
        housing_type="apartment"
    )
    assert any("borewell" in a.lower() for a in res_borewell["actions"])
    assert any("rwa" in a.lower() or "apartment" in a.lower() for a in res_borewell["actions"])
    assert "Borewell Setup" in res_borewell["tailored_tags"]

    # Tanker + Independent
    res_tanker = tailor_actions_for_profile(
        base_actions=base_actions,
        category="water_supply",
        water_source="tanker",
        housing_type="independent"
    )
    assert any("tanker" in a.lower() for a in res_tanker["actions"])
    assert any("motor" in a.lower() or "sump" in a.lower() for a in res_tanker["actions"])
    assert "Tanker Reliant" in res_tanker["tailored_tags"]


def test_personalization_power_cut_vulnerabilities():
    """Verify power cut checklist adapts to dialysis, WFH, and elderly modes."""
    base_actions = ["Turn off sensitive appliances."]

    res_vuln = tailor_actions_for_profile(
        base_actions=base_actions,
        category="power_cut",
        housing_type="apartment",
        vulnerable_modes=["dialysis", "wfh"]
    )
    assert any("dialysis" in a.lower() or "medical" in a.lower() for a in res_vuln["actions"])
    assert any("hotspot" in a.lower() or "ups" in a.lower() for a in res_vuln["actions"])
    assert "Critical Medical Support" in res_vuln["tailored_tags"]
    assert "WFH Continuity" in res_vuln["tailored_tags"]


def test_saved_locations_crud(db_session: Session):
    """Test saving, retrieving, and deleting multiple locations via CRUD."""
    user_id = "test_citizen_42"

    # 1. Add Home location in Gachibowli
    home = crud.create_saved_location(
        db=db_session,
        label="Home",
        locality_name="Gachibowli",
        lat=17.4401,
        lng=78.3489,
        radius_km=4.0,
        user_id=user_id
    )
    assert home.id is not None
    assert home.label == "Home"
    assert home.locality_name == "Gachibowli"

    # 2. Add Office location in Hitec City
    office = crud.create_saved_location(
        db=db_session,
        label="Office",
        locality_name="Hitec City",
        lat=17.4435,
        lng=78.3772,
        radius_km=3.0,
        user_id=user_id
    )
    assert office.id is not None

    # 3. Retrieve saved locations
    locations = crud.get_saved_locations(db=db_session, user_id=user_id)
    assert len(locations) >= 2
    labels = [l.label for l in locations]
    assert "Home" in labels
    assert "Office" in labels

    # 4. Delete Office location
    deleted = crud.delete_saved_location(db=db_session, location_id=office.id, user_id=user_id)
    assert deleted is True

    # 5. Verify office is removed
    remaining = crud.get_saved_locations(db=db_session, user_id=user_id)
    remaining_labels = [l.label for l in remaining]
    assert "Office" not in remaining_labels
    assert "Home" in remaining_labels


def test_user_profile_crud(db_session: Session):
    """Test updating and fetching citizen household personalization profile."""
    user_id = "test_citizen_profile_crud"

    # Upsert profile
    prof = crud.upsert_user_profile(
        db=db_session,
        user_id=user_id,
        water_source="tanker",
        housing_type="independent",
        vulnerable_modes=["elderly", "wfh"],
        preferred_language="te"
    )
    assert prof.water_source == "tanker"
    assert prof.housing_type == "independent"
    assert prof.preferred_language == "te"

    # Fetch profile
    fetched = crud.get_user_profile(db=db_session, user_id=user_id)
    assert fetched.water_source == "tanker"
    assert fetched.housing_type == "independent"
    assert "elderly" in json.loads(fetched.vulnerable_modes)
