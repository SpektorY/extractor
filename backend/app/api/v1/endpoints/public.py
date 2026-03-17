from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import create_volunteer_token
from app.models import Event, Volunteer, EventVolunteer
from app.schemas.volunteer import VolunteerResponse
from app.schemas.volunteer_signup import VolunteerSignupCreate

router = APIRouter()


class EventJoinPublicResponse(BaseModel):
    """Minimal event info for the join page (no auth)."""

    id: int
    name: str
    address: str
    description: Optional[str] = None


class JoinEventRequest(BaseModel):
    """Phone required; details required only when volunteer is new."""

    phone: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    area: Optional[str] = None
    group_tag: Optional[str] = None


class JoinEventResponse(BaseModel):
    magic_token: str
    attendance_status: Optional[str] = None


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
            status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא"
        )
    return event


@router.get("/event/{event_id}", response_model=EventJoinPublicResponse)
def get_event_public(
    event_id: int, db: Session = Depends(get_db)
) -> EventJoinPublicResponse:
    """Public: minimal event info for the volunteer join page (no auth)."""
    event = get_public_joinable_event(event_id, db)
    return EventJoinPublicResponse(
        id=event.id,
        name=event.name,
        address=event.address,
        description=event.description or None,
    )


@router.post("/event/{event_id}/join")
def join_event(
    event_id: int,
    body: JoinEventRequest,
    db: Session = Depends(get_db),
):
    """
    Volunteer joins event by link: submit phone. If existing volunteer (by phone),
    attach to event if needed and return volunteer token. If new volunteer, return need_details
    and frontend shows form; then POST again with first_name (and optional details).
    """
    get_public_joinable_event(event_id, db)

    phone = (body.phone or "").strip()
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="נא להזין טלפון"
        )

    volunteer = (
        db.query(Volunteer)
        .filter(Volunteer.phone == phone, Volunteer.deleted_at.is_(None))
        .first()
    )

    if volunteer:
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

    # New volunteer: require first_name
    if not (body.first_name or "").strip():
        return {"need_details": True}

    volunteer = Volunteer(
        first_name=(body.first_name or "").strip(),
        last_name=(body.last_name or "").strip() or "",
        phone=phone,
        group_tag=body.group_tag,
        living_area=body.area,
    )
    db.add(volunteer)
    db.flush()
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


@router.post(
    "/volunteer-signup",
    response_model=VolunteerResponse,
    status_code=status.HTTP_201_CREATED,
)
def volunteer_signup(
    body: VolunteerSignupCreate, db: Session = Depends(get_db)
) -> VolunteerResponse:
    """Public self-signup: adds a volunteer."""
    existing = (
        db.query(Volunteer)
        .filter(
            Volunteer.phone == body.phone,
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
        phone=body.phone,
        group_tag=body.group_tag,
        living_area=body.area,
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    return VolunteerResponse.model_validate(volunteer)
