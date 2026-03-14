from typing import Optional, List
from pydantic import BaseModel


class ResidentRow(BaseModel):
    """One row from Excel for import"""
    first_name: str
    last_name: str
    address: str
    phone: Optional[str] = None
    notes: Optional[str] = None


class ResidentsUploadResult(BaseModel):
    imported: int
    errors: List[str] = []
