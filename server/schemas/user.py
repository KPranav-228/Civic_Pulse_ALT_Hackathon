"""Pydantic schemas for Citizen Profile and Personalization."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserProfileBase(BaseModel):
    water_source: str = Field(
        default="municipal",
        description="Primary water source: municipal, borewell, tanker, or mixed"
    )
    housing_type: str = Field(
        default="apartment",
        description="Housing structure: apartment, independent, or villa"
    )
    vulnerable_modes: List[str] = Field(
        default_factory=list,
        description="Vulnerable conditions: dialysis, home_oxygen, elderly, wfh"
    )
    preferred_language: str = Field(
        default="en",
        description="Preferred delivery language: en, te, or hi"
    )


class UserProfileUpdate(BaseModel):
    user_id: Optional[str] = Field(default="default_user")
    water_source: Optional[str] = None
    housing_type: Optional[str] = None
    vulnerable_modes: Optional[List[str]] = None
    preferred_language: Optional[str] = None


class UserProfileResponse(UserProfileBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
