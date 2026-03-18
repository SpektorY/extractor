from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.volunteer import VolunteerStatus


class VolunteerBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    group_tag: Optional[str] = None
    living_area: Optional[str] = None


class VolunteerCreate(VolunteerBase):
    pass


class VolunteerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    group_tag: Optional[str] = None
    living_area: Optional[str] = None


class VolunteerResponse(VolunteerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    anonymized: bool = False
    status: VolunteerStatus = VolunteerStatus.PENDING
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = (
        None  # set when soft-deleted; list can include_deleted to still show for anonymize
    )
