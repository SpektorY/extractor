from sqlalchemy import Column, Integer, String, Text, DateTime
from app.models.base import TimestampMixin
from app.core.database import Base


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # legacy soft delete
