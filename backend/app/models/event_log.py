from sqlalchemy import Column, Integer, Text, ForeignKey, Enum as SQLEnum
import enum
from app.models.base import TimestampMixin
from app.core.database import Base


class EventLogAuthorType(str, enum.Enum):
    ADMIN = "admin"
    VOLUNTEER = "volunteer"


class EventLog(Base, TimestampMixin):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    author_type = Column(SQLEnum(EventLogAuthorType), nullable=False)
    author_volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True)  # if volunteer
