from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.models.base import TimestampMixin
from app.core.database import Base


class Volunteer(Base, TimestampMixin):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False, unique=True, index=True)
    group_tag = Column(String(100), nullable=True)  # e.g. "רפואה", "סיירת שכונתית"
    living_area = Column(String(200), nullable=True)  # אזור מגורים
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # soft delete
    anonymized = Column(
        Boolean, default=False, nullable=False
    )  # GDPR: personal data wiped
