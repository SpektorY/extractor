from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum
import enum
from app.models.base import TimestampMixin
from app.core.database import Base


class ResidentStatus(str, enum.Enum):
    UNCHECKED = "unchecked"       # טרם נבדק
    HEALTHY = "healthy"           # בריא
    INJURED = "injured"           # נפגע
    EVACUATED = "evacuated"       # פונה לטיפול רפואי
    ABSENT = "absent"             # נעדר


class ResidentSource(str, enum.Enum):
    UPLOADED = "uploaded"   # from admin file
    CASUAL = "casual"       # added in field by volunteer (מזדמן)


class Resident(Base, TimestampMixin):
    __tablename__ = "residents"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    # Name: first_name + last_name (uploaded); casuals use first_name only, last_name null
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    address = Column(String(500), nullable=False)
    phone = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)  # pre-event notes
    status = Column(SQLEnum(ResidentStatus), default=ResidentStatus.UNCHECKED, nullable=False)
    volunteer_notes = Column(Text, nullable=True)  # note from volunteer who updated
    source = Column(String(20), default=ResidentSource.UPLOADED.value, nullable=False)
    updated_by_volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True)
    created_by_volunteer_id = Column(Integer, ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True)
