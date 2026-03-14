from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.security import create_magic_link_token, decode_access_token
from app.models import Event, User, Resident, Volunteer, EventVolunteer, EventLog
from app.models.event_volunteer import VolunteerEventStatus
from app.schemas.event import EventCreate, EventResponse, EventVolunteersAttach
from app.schemas.resident import ResidentsUploadResult
from app.schemas.control_room import (
    ResidentListRow,
    EventVolunteerRow,
    EventLogRow,
    EventLogCreate,
)
from app.api.v1.endpoints.auth import get_current_user
from app.services.excel_import import parse_residents_file
from app.services.excel_export import export_event_to_excel
from fastapi.responses import StreamingResponse
from app.models.event_log import EventLogAuthorType
from app.services.event_broadcast import subscribe, unsubscribe, broadcast_event_updated_sync

router = APIRouter()


@router.websocket("/{event_id}/ws")
async def event_control_room_ws(websocket: WebSocket, event_id: int):
    """Admin control room: subscribe to live updates for this event (residents, casuals, log)."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    sub = decode_access_token(token)
    if not sub:
        await websocket.close(code=4001)
        return
    try:
        user_id = int(sub)
    except ValueError:
        await websocket.close(code=4001)
        return
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
        if not user:
            await websocket.close(code=4001)
            return
        event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
        if not event:
            await websocket.close(code=4004)
            return
    finally:
        db.close()
    await websocket.accept()
    await subscribe(event_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await unsubscribe(event_id, websocket)


@router.get("", response_model=List[EventResponse])
def list_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[EventResponse]:
    events = (
        db.query(Event)
        .filter(Event.deleted_at.is_(None))
        .order_by(Event.created_at.desc())
    )
    return [EventResponse.model_validate(e) for e in events]


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    body: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventResponse:
    event = Event(
        name=body.name,
        address=body.address,
        description=body.description,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return EventResponse.model_validate(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    from datetime import datetime, timezone
    event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא")
    event.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return None


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventResponse:
    event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא")
    return EventResponse.model_validate(event)


@router.post("/{event_id}/residents/upload", response_model=ResidentsUploadResult)
def upload_residents(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResidentsUploadResult:
    event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא")
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="נדרש קובץ")
    content = file.file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="קובץ גדול מדי")
    rows, errors = parse_residents_file(content, file.filename)
    if not rows and errors and not any("שורה" in e for e in errors):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors[0] if errors else "קובץ לא תקין")
    for r in rows:
        resident = Resident(
            event_id=event_id,
            first_name=r.first_name,
            last_name=r.last_name,
            address=r.address,
            phone=r.phone,
            notes=r.notes,
        )
        db.add(resident)
    db.commit()
    broadcast_event_updated_sync(event_id)
    return ResidentsUploadResult(imported=len(rows), errors=errors)


@router.post("/{event_id}/volunteers")
def attach_volunteers(
    event_id: int,
    body: EventVolunteersAttach,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    from app.core.config import settings
    from app.services.whatsapp import send_volunteer_invite

    event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא")
    volunteers = db.query(Volunteer).filter(
        Volunteer.id.in_(body.volunteer_ids),
        Volunteer.deleted_at.is_(None),
    ).all()
    added_pairs: list[tuple[EventVolunteer, Volunteer]] = []
    for v in volunteers:
        existing = db.query(EventVolunteer).filter(
            EventVolunteer.event_id == event_id,
            EventVolunteer.volunteer_id == v.id,
        ).first()
        if not existing:
            ev = EventVolunteer(
                event_id=event_id,
                volunteer_id=v.id,
                magic_token=create_magic_link_token(),
                status=VolunteerEventStatus.PENDING,
            )
            db.add(ev)
            added_pairs.append((ev, v))
    db.commit()
    # Send WhatsApp invite to each newly attached volunteer
    base_url = settings.frontend_base_url.rstrip("/")
    invites_sent = 0
    for ev, v in added_pairs:
        link = f"{base_url}/event/{ev.magic_token}"
        if send_volunteer_invite(v.phone, event.name, event.address, link):
            invites_sent += 1
    return {"attached": len(added_pairs), "invites_sent": invites_sent}


@router.post("/{event_id}/send-invites")
def send_invites(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    from app.core.config import settings
    from app.services.whatsapp import send_volunteer_invite
    event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא")
    evs = db.query(EventVolunteer, Volunteer).join(Volunteer, EventVolunteer.volunteer_id == Volunteer.id).filter(
        EventVolunteer.event_id == event_id,
    ).all()
    base_url = settings.frontend_base_url.rstrip("/")
    sent = 0
    for ev, v in evs:
        link = f"{base_url}/event/{ev.magic_token}"
        if send_volunteer_invite(v.phone, event.name, event.address, link):
            sent += 1
    return {"sent": sent, "total": len(evs)}


@router.get("/{event_id}/export-excel")
def export_event_excel(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא")
    residents = db.query(Resident).filter(Resident.event_id == event_id).all()
    logs = db.query(EventLog).filter(EventLog.event_id == event_id).order_by(EventLog.created_at.asc()).all()
    buffer = export_event_to_excel(event, residents, logs)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=event-{event_id}.xlsx"},
    )


@router.get("/{event_id}/residents", response_model=List[ResidentListRow])
def list_event_residents(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ResidentListRow]:
    event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא")
    rows = db.query(Resident).filter(Resident.event_id == event_id).all()
    return [
        ResidentListRow(
            id=r.id,
            first_name=r.first_name,
            last_name=r.last_name,
            address=r.address,
            status=r.status.value,
            volunteer_notes=r.volunteer_notes,
            source=r.source,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.get("/{event_id}/event-volunteers", response_model=List[EventVolunteerRow])
def list_event_volunteers(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[EventVolunteerRow]:
    event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא")
    evs = db.query(EventVolunteer, Volunteer).join(Volunteer, EventVolunteer.volunteer_id == Volunteer.id).filter(
        EventVolunteer.event_id == event_id,
    ).all()
    return [
        EventVolunteerRow(
            id=ev.id,
            volunteer_id=ev.volunteer_id,
            volunteer_name=f"{v.first_name} {v.last_name}",
            status=ev.status.value,
            magic_token=ev.magic_token,
        )
        for ev, v in evs
    ]


@router.get("/{event_id}/log", response_model=List[EventLogRow])
def list_event_log(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[EventLogRow]:
    event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא")
    rows = db.query(EventLog).filter(EventLog.event_id == event_id).order_by(EventLog.created_at.asc()).all()
    return [
        EventLogRow(id=r.id, message=r.message, author_type=r.author_type.value, created_at=r.created_at)
        for r in rows
    ]


@router.post("/{event_id}/log", response_model=EventLogRow, status_code=status.HTTP_201_CREATED)
def add_event_log(
    event_id: int,
    body: EventLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventLogRow:
    event = db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None)).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא")
    log = EventLog(
        event_id=event_id,
        message=body.message,
        author_type=EventLogAuthorType.ADMIN,
        author_user_id=current_user.id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    broadcast_event_updated_sync(event_id)
    return EventLogRow(id=log.id, message=log.message, author_type=log.author_type.value, created_at=log.created_at)
