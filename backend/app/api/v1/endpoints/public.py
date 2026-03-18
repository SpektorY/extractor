import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import VolunteerAuth, get_optional_current_volunteer
from app.core.config import settings
from app.core.database import get_db
from app.core.security import ROLE_VOLUNTEER, create_access_token, create_volunteer_token
from app.models import Event, EventVolunteer, Volunteer, VolunteerOtp, VolunteerStatus
from app.schemas.volunteer import VolunteerResponse
from app.schemas.volunteer_signup import VolunteerSignupCreate
from app.services.sms import normalize_phone_for_storage, send_otp_sms

router = APIRouter()


class EventJoinPublicResponse(BaseModel):
    id: int
    name: str
    address: str
    description: Optional[str] = None


class JoinEventRequest(BaseModel):
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    area: Optional[str] = None
    group_tag: Optional[str] = None


class JoinEventResponse(BaseModel):
    magic_token: str
    attendance_status: Optional[str] = None


class OtpRequest(BaseModel):
    phone: str


class OtpVerifyRequest(BaseModel):
    phone: str
    code: str


class VolunteerAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    volunteer: VolunteerResponse


def _normalize_phone(raw_phone: str) -> str:
    try:
        return normalize_phone_for_storage(raw_phone)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _generate_otp_code() -> str:
    n = max(4, min(8, settings.otp_code_length))
    low = 10 ** (n - 1)
    high = (10**n) - 1
    return str(random.randint(low, high))


def get_public_joinable_event(event_id: int, db: Session) -> Event:
    event = (
        db.query(Event)
        .filter(
            Event.id == event_id,
            Event.deleted_at.is_(None),
            Event.archived_at.is_(None),
        )
        .first()
    )
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="אירוע לא נמצא",
        )
    return event


@router.get("/event/{event_id}", response_model=EventJoinPublicResponse)
def get_event_public(event_id: int, db: Session = Depends(get_db)) -> EventJoinPublicResponse:
    event = get_public_joinable_event(event_id, db)
    return EventJoinPublicResponse(
        id=event.id,
        name=event.name,
        address=event.address,
        description=event.description or None,
    )


@router.post("/event/{event_id}/join", response_model=JoinEventResponse)
def join_event(
    event_id: int,
    body: JoinEventRequest,
    db: Session = Depends(get_db),
    volunteer_auth: Optional[VolunteerAuth] = Depends(get_optional_current_volunteer),
):
    get_public_joinable_event(event_id, db)

    if not volunteer_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "נדרשת התחברות", "code": "LOGIN_REQUIRED"},
        )

    volunteer = (
        db.query(Volunteer)
        .filter(
            Volunteer.id == volunteer_auth.volunteer_id,
            Volunteer.deleted_at.is_(None),
        )
        .first()
    )
    if not volunteer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "נדרשת התחברות מחדש", "code": "LOGIN_REQUIRED"},
        )

    if volunteer.status != VolunteerStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "החשבון ממתין לאישור מנהל", "code": "PENDING_APPROVAL"},
        )

    if body.phone and _normalize_phone(body.phone) != volunteer.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="מספר טלפון לא תואם לחשבון המחובר",
        )

    ev = (
        db.query(EventVolunteer)
        .filter(
            EventVolunteer.event_id == event_id,
            EventVolunteer.volunteer_id == volunteer.id,
        )
        .first()
    )
    if not ev:
        ev = EventVolunteer(
            event_id=event_id,
            volunteer_id=volunteer.id,
            magic_token=create_volunteer_token(),
        )
        db.add(ev)
        db.commit()
        db.refresh(ev)

    return JoinEventResponse(
        magic_token=ev.magic_token,
        attendance_status=ev.status.value if ev.status else None,
    )


@router.post("/volunteer-signup", response_model=VolunteerResponse, status_code=status.HTTP_201_CREATED)
def volunteer_signup(body: VolunteerSignupCreate, db: Session = Depends(get_db)) -> VolunteerResponse:
    phone = _normalize_phone(body.phone)
    existing = (
        db.query(Volunteer)
        .filter(
            Volunteer.phone == phone,
            Volunteer.deleted_at.is_(None),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="טלפון זה כבר רשום במערכת",
        )
    volunteer = Volunteer(
        first_name=body.first_name,
        last_name=body.last_name or "",
        phone=phone,
        group_tag=body.group_tag,
        living_area=body.area,
        status=VolunteerStatus.PENDING,
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    return VolunteerResponse.model_validate(volunteer)


@router.post("/auth/request-otp")
def request_otp(body: OtpRequest, db: Session = Depends(get_db)) -> dict:
    phone = _normalize_phone(body.phone)
    if not phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="נא להזין טלפון")

    code = _generate_otp_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expiry_minutes)
    db.query(VolunteerOtp).filter(VolunteerOtp.phone == phone).delete()
    db.add(VolunteerOtp(phone=phone, code=code, expires_at=expires_at))
    db.commit()
    send_otp_sms(phone, code)
    return {"ok": True}


@router.post("/auth/verify-otp", response_model=VolunteerAuthResponse)
def verify_otp(body: OtpVerifyRequest, db: Session = Depends(get_db)) -> VolunteerAuthResponse:
    phone = _normalize_phone(body.phone)
    code = (body.code or "").strip()
    if not phone or not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="טלפון או קוד חסרים")

    otp = (
        db.query(VolunteerOtp)
        .filter(VolunteerOtp.phone == phone, VolunteerOtp.code == code)
        .order_by(VolunteerOtp.created_at.desc())
        .first()
    )
    now = datetime.now(timezone.utc)
    if not otp or otp.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="קוד לא תקין או שפג תוקפו",
        )

    volunteer = (
        db.query(Volunteer)
        .filter(Volunteer.phone == phone, Volunteer.deleted_at.is_(None))
        .first()
    )
    if not volunteer:
        volunteer = Volunteer(
            first_name="משתמש",
            last_name="",
            phone=phone,
            status=VolunteerStatus.PENDING,
        )
        db.add(volunteer)
        db.flush()

    db.query(VolunteerOtp).filter(VolunteerOtp.phone == phone).delete()
    db.commit()
    db.refresh(volunteer)

    token = create_access_token(subject=volunteer.id, role=ROLE_VOLUNTEER)
    return VolunteerAuthResponse(
        access_token=token,
        volunteer=VolunteerResponse.model_validate(volunteer),
    )


@router.get("/auth/me", response_model=VolunteerResponse)
def get_me(
    db: Session = Depends(get_db),
    volunteer_auth: Optional[VolunteerAuth] = Depends(get_optional_current_volunteer),
) -> VolunteerResponse:
    if not volunteer_auth:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="נדרשת התחברות")

    volunteer = (
        db.query(Volunteer)
        .filter(
            Volunteer.id == volunteer_auth.volunteer_id,
            Volunteer.deleted_at.is_(None),
        )
        .first()
    )
    if not volunteer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="מתנדב לא נמצא")
    return VolunteerResponse.model_validate(volunteer)
