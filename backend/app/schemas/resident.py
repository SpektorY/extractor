from typing import Optional, List
from pydantic import BaseModel


class ResidentRow(BaseModel):
    """One row from Excel for import"""
    identity_number: str
    gender: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    apartment: Optional[str] = None
    age: Optional[int] = None
    first_name: str
    last_name: str
    address: str
    phone: Optional[str] = None
    home_phone: Optional[str] = None
    notes: Optional[str] = None


class ResidentsUploadResult(BaseModel):
    imported: int
    errors: List[str] = []
