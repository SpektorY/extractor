"""Schema for public volunteer self-signup (writes to volunteers table)."""
from typing import Optional
from pydantic import BaseModel


class VolunteerSignupCreate(BaseModel):
    """Public form: first_name, last_name (optional), phone, area (→ living_area), group_tag (optional)."""
    first_name: str
    last_name: Optional[str] = None
    phone: str
    area: Optional[str] = None  # living_area
    group_tag: Optional[str] = None
