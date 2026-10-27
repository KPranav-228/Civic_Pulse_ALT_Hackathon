"""Pydantic schemas for Saved Locations (hyperlocal zones)."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SavedLocationBase(BaseModel):
    label: str = Field(..., json_schema_extra={"example": "Home"}, description="Label such as Home, Office, Parents, School")
    locality_name: str = Field(..., json_schema_extra={"example": "Gachibowli"}, description="Locality or landmark name")
    lat: float = Field(..., json_schema_extra={"example": 17.4401}, description="Latitude")
    lng: float = Field(..., json_schema_extra={"example": 78.3489}, description="Longitude")
    radius_km: float = Field(default=5.0, ge=0.5, le=50.0, description="Alert monitoring radius in kilometers")


class SavedLocationCreate(SavedLocationBase):
    user_id: Optional[str] = Field(default="default_user", description="Citizen account or device ID")


class SavedLocationResponse(SavedLocationBase):
    id: int
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
