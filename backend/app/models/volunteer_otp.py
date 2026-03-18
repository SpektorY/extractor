from sqlalchemy import Column, DateTime, Integer, String, func

from app.core.database import Base


class VolunteerOtp(Base):
    __tablename__ = "volunteer_otps"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), nullable=False, index=True)
    code = Column(String(10), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
