import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from app.models.base import TimestampMixin
from app.core.database import Base


class VolunteerAttendanceStatus(str, enum.Enum):
    COMING = "coming"
    NOT_COMING = "not_coming"
    ARRIVED = "arrived"
    LEFT = "left"


class EventVolunteer(Base, TimestampMixin):
    __tablename__ = "event_volunteers"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False)
    magic_token = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(Enum(VolunteerAttendanceStatus, name="volunteereventstatus"), nullable=True)
