from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
import enum
from app.models.base import TimestampMixin
from app.core.database import Base


class VolunteerEventStatus(str, enum.Enum):
    PENDING = "pending"           # טרם הגיב
    COMING = "coming"             # מגיע
    NOT_COMING = "not_coming"    # לא מגיע
    ARRIVED = "arrived"          # הגיע לאירוע


class EventVolunteer(Base, TimestampMixin):
    __tablename__ = "event_volunteers"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False)
    magic_token = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(VolunteerEventStatus), default=VolunteerEventStatus.PENDING, nullable=False)
