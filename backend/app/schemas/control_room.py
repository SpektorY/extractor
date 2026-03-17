from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ResidentListRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: str
    status: str
    volunteer_notes: Optional[str] = None
    source: str  # "uploaded" | "casual"
    updated_at: Optional[datetime] = None


class EventVolunteerRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    volunteer_id: int
    volunteer_name: str
    volunteer_phone: Optional[str] = None
    magic_token: str
    status: Optional[str] = None
    updated_at: Optional[datetime] = None


class ControlRoomSummary(BaseModel):
    total_residents: int
    unchecked_residents: int
    critical_residents: int
    arrived_volunteers: int
    not_coming_volunteers: int
    casual_residents: int


class EventLogRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    message: str
    author_type: str
    author_name: Optional[str] = None
    created_at: Optional[datetime] = None


class EventLogCreate(BaseModel):
    message: str
