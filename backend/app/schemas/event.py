from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class EventBase(BaseModel):
    name: str
    address: str
    description: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None


class EventVolunteersAttach(BaseModel):
    volunteer_ids: List[int]
