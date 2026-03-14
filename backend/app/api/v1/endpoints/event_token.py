"""Public endpoints for volunteers using magic link token (no admin JWT)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models import Event, EventVolunteer, Resident, EventLog
from app.models.resident import ResidentStatus, ResidentSource
from app.models.event_volunteer import VolunteerEventStatus
from app.models.event_log import EventLogAuthorType
from app.services.event_broadcast import broadcast_event_updated_sync

router = APIRouter()


class EventByTokenResponse(BaseModel):
    event_id: int
    event_name: str
    event_address: str
    event_description: Optional[str] = None
    volunteer_status: str  # e.g. coming, arrived, pending


def get_event_volunteer_by_token(
    token: str,
    db: Session = Depends(get_db),
) -> EventVolunteer:
    ev = db.query(EventVolunteer).filter(EventVolunteer.magic_token == token).first()
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="קישור לא תקין או שפג תוקפו"
        )
    event = (
        db.query(Event)
        .filter(Event.id == ev.event_id, Event.deleted_at.is_(None))
        .first()
    )
    if not event:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="האירוע הסתיים או בוטל. תודה שהתנדבת!",
        )
    return ev


@router.get("/event-by-token/{token}", response_model=EventByTokenResponse)
def get_event_by_token(
    token: str,
    db: Session = Depends(get_db),
) -> EventByTokenResponse:
    ev = get_event_volunteer_by_token(token, db)
    event = db.query(Event).filter(Event.id == ev.event_id).first()
    return EventByTokenResponse(
        event_id=event.id,
        event_name=event.name,
        event_address=event.address,
        event_description=event.description or None,
        volunteer_status=ev.status.value,
    )


class RespondRequest(BaseModel):
    coming: bool


@router.post("/event-by-token/{token}/respond")
def respond_to_event(
    token: str,
    body: RespondRequest,
    db: Session = Depends(get_db),
) -> dict:
    ev = get_event_volunteer_by_token(token, db)
    ev.status = (
        VolunteerEventStatus.COMING if body.coming else VolunteerEventStatus.NOT_COMING
    )
    db.commit()
    return {"status": ev.status.value}


class ResidentRow(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: str
    status: str
    volunteer_notes: Optional[str] = None
    source: str


@router.get("/event-by-token/{token}/residents", response_model=List[ResidentRow])
def get_residents_by_token(
    token: str, db: Session = Depends(get_db)
) -> List[ResidentRow]:
    ev = get_event_volunteer_by_token(token, db)
    rows = db.query(Resident).filter(Resident.event_id == ev.event_id).all()
    return [
        ResidentRow(
            id=r.id,
            first_name=r.first_name,
            last_name=r.last_name,
            address=r.address,
            status=r.status.value,
            volunteer_notes=r.volunteer_notes,
            source=r.source,
        )
        for r in rows
    ]


@router.post("/event-by-token/{token}/arrived")
def mark_arrived(token: str, db: Session = Depends(get_db)) -> dict:
    ev = get_event_volunteer_by_token(token, db)
    ev.status = VolunteerEventStatus.ARRIVED
    db.commit()
    return {"status": ev.status.value}


class ResidentUpdateRequest(BaseModel):
    status: str  # unchecked, healthy, injured, evacuated, absent
    volunteer_notes: Optional[str] = None


@router.patch("/event-by-token/{token}/residents/{resident_id}")
def update_resident(
    token: str,
    resident_id: int,
    body: ResidentUpdateRequest,
    db: Session = Depends(get_db),
) -> dict:
    ev = get_event_volunteer_by_token(token, db)
    resident = (
        db.query(Resident)
        .filter(
            Resident.id == resident_id,
            Resident.event_id == ev.event_id,
        )
        .first()
    )
    if not resident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="תושב לא נמצא"
        )
    from app.models.resident import ResidentStatus

    try:
        resident.status = ResidentStatus(body.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="סטטוס לא תקין"
        )
    resident.volunteer_notes = body.volunteer_notes
    resident.updated_by_volunteer_id = ev.volunteer_id
    db.commit()
    broadcast_event_updated_sync(ev.event_id)
    return {"status": resident.status.value}


class AddResidentRequest(BaseModel):
    """Add a resident (casual) from the field. Name stored as first_name (last_name null)."""

    first_name: str
    last_name: str
    address: str
    phone: Optional[str] = None
    status: str = "unchecked"
    notes: Optional[str] = None


class AddResidentResponse(BaseModel):
    id: int


@router.post(
    "/event-by-token/{token}/residents",
    response_model=AddResidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_resident_by_token(
    token: str,
    body: AddResidentRequest,
    db: Session = Depends(get_db),
) -> AddResidentResponse:
    """Add a casual resident (מזדמן) from the field."""
    ev = get_event_volunteer_by_token(token, db)
    try:
        status_enum = ResidentStatus(body.status)
    except ValueError:
        status_enum = ResidentStatus.UNCHECKED
    r = Resident(
        event_id=ev.event_id,
        first_name=body.first_name,
        last_name=body.last_name,
        address=body.address,
        phone=body.phone,
        status=status_enum,
        volunteer_notes=body.notes,
        source=ResidentSource.CASUAL.value,
        created_by_volunteer_id=ev.volunteer_id,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    broadcast_event_updated_sync(ev.event_id)
    return AddResidentResponse(id=r.id)


class LogEntry(BaseModel):
    id: int
    message: str
    author_type: str
    created_at: Optional[str] = None


@router.get("/event-by-token/{token}/log", response_model=List[LogEntry])
def get_event_log(token: str, db: Session = Depends(get_db)) -> List[LogEntry]:
    ev = get_event_volunteer_by_token(token, db)
    rows = (
        db.query(EventLog)
        .filter(EventLog.event_id == ev.event_id)
        .order_by(EventLog.created_at.asc())
        .all()
    )
    return [
        LogEntry(
            id=r.id,
            message=r.message,
            author_type=r.author_type.value,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in rows
    ]


class LogCreate(BaseModel):
    message: str


@router.post(
    "/event-by-token/{token}/log",
    response_model=LogEntry,
    status_code=status.HTTP_201_CREATED,
)
def add_event_log(
    token: str,
    body: LogCreate,
    db: Session = Depends(get_db),
) -> LogEntry:
    ev = get_event_volunteer_by_token(token, db)
    log = EventLog(
        event_id=ev.event_id,
        message=body.message,
        author_type=EventLogAuthorType.VOLUNTEER,
        author_volunteer_id=ev.volunteer_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    broadcast_event_updated_sync(ev.event_id)
    return LogEntry(
        id=log.id,
        message=log.message,
        author_type=log.author_type.value,
        created_at=log.created_at.isoformat() if log.created_at else None,
    )
