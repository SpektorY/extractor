from datetime import datetime, timezone
from typing import List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.security import create_volunteer_token, decode_access_token
from app.models import Event, Resident, Volunteer, EventVolunteer, EventLog
from app.schemas.event import EventCreate, EventResponse, EventVolunteersAttach
from app.schemas.resident import ResidentsUploadResult
from app.schemas.control_room import (
    ControlRoomSummary,
    ResidentListRow,
    EventVolunteerRow,
    EventLogRow,
    EventLogCreate,
)
from app.api.v1.endpoints.auth import get_current_user, AdminAuth
from app.services.excel_import import parse_residents_file
from app.services.excel_export import export_event_to_excel
from fastapi.responses import StreamingResponse
from app.models.event_log import EventLogAuthorType
from app.models.event_volunteer import VolunteerAttendanceStatus
from app.models.resident import ResidentStatus, ResidentSource
from app.services.event_broadcast import (
    subscribe,
    unsubscribe,
    broadcast_event_updated_sync,
)

router = APIRouter()


def get_admin_event_or_404(
    db: Session,
    event_id: int,
    *,
    require_active: bool = False,
) -> Event:
    query = db.query(Event).filter(
        Event.id == event_id,
        Event.deleted_at.is_(None),
    )
    if require_active:
        query = query.filter(Event.archived_at.is_(None))
    event = query.first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="אירוע לא נמצא"
        )
    return event


@router.websocket("/{event_id}/ws")
async def event_control_room_ws(websocket: WebSocket, event_id: int):
    """Admin control room: subscribe to live updates for this event (residents, casuals, log)."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    from app.core.security import ADMIN_SUB

    sub = decode_access_token(token)
    if sub != ADMIN_SUB:
        await websocket.close(code=4001)
        return
    db = SessionLocal()
    try:
        event = (
            db.query(Event)
            .filter(Event.id == event_id, Event.deleted_at.is_(None))
            .first()
        )
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
    current_user: AdminAuth = Depends(get_current_user),
) -> List[EventResponse]:
    events = (
        db.query(Event)
        .filter(Event.deleted_at.is_(None))
        .order_by(Event.created_at.desc())
        .all()
    )
    return [EventResponse.model_validate(e) for e in events]


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    body: EventCreate,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
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


@router.post("/{event_id}/close", response_model=EventResponse)
def close_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> EventResponse:
    event = get_admin_event_or_404(db, event_id, require_active=True)
    event.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)
    broadcast_event_updated_sync(event_id)
    return EventResponse.model_validate(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> None:
    event = get_admin_event_or_404(db, event_id, require_active=True)
    event.archived_at = datetime.now(timezone.utc)
    db.commit()
    broadcast_event_updated_sync(event_id)
    return None


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> EventResponse:
    event = get_admin_event_or_404(db, event_id)
    return EventResponse.model_validate(event)


@router.get("/{event_id}/summary", response_model=ControlRoomSummary)
def get_control_room_summary(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> ControlRoomSummary:
    get_admin_event_or_404(db, event_id)

    residents = db.query(Resident).filter(Resident.event_id == event_id).all()
    volunteers = (
        db.query(EventVolunteer)
        .filter(EventVolunteer.event_id == event_id)
        .all()
    )

    critical_statuses = {
        ResidentStatus.INJURED,
        ResidentStatus.EVACUATED,
        ResidentStatus.ABSENT,
    }

    return ControlRoomSummary(
        total_residents=len(residents),
        unchecked_residents=sum(
            1 for resident in residents if resident.status == ResidentStatus.UNCHECKED
        ),
        critical_residents=sum(
            1 for resident in residents if resident.status in critical_statuses
        ),
        arrived_volunteers=sum(
            1
            for volunteer in volunteers
            if volunteer.status == VolunteerAttendanceStatus.ARRIVED
        ),
        not_coming_volunteers=sum(
            1
            for volunteer in volunteers
            if volunteer.status == VolunteerAttendanceStatus.NOT_COMING
        ),
        casual_residents=sum(
            1 for resident in residents if resident.source == ResidentSource.CASUAL.value
        ),
    )


@router.post("/{event_id}/residents/upload", response_model=ResidentsUploadResult)
def upload_residents(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> ResidentsUploadResult:
    get_admin_event_or_404(db, event_id, require_active=True)
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="נדרש קובץ")
    content = file.file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="קובץ גדול מדי"
        )
    rows, errors = parse_residents_file(content, file.filename)
    if not rows and errors and not any("שורה" in e for e in errors):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0] if errors else "קובץ לא תקין",
        )
    for r in rows:
        resident = Resident(
            event_id=event_id,
            identity_number=r.identity_number,
            first_name=r.first_name,
            last_name=r.last_name,
            gender=r.gender,
            city=r.city,
            street=r.street,
            house_number=r.house_number,
            apartment=r.apartment,
            age=r.age,
            address=r.address,
            phone=r.phone,
            home_phone=r.home_phone,
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
    current_user: AdminAuth = Depends(get_current_user),
) -> dict:
    get_admin_event_or_404(db, event_id, require_active=True)
    volunteers = (
        db.query(Volunteer)
        .filter(
            Volunteer.id.in_(body.volunteer_ids),
            Volunteer.deleted_at.is_(None),
        )
        .all()
    )
    added = 0
    for v in volunteers:
        existing = (
            db.query(EventVolunteer)
            .filter(
                EventVolunteer.event_id == event_id,
                EventVolunteer.volunteer_id == v.id,
            )
            .first()
        )
        if not existing:
            ev = EventVolunteer(
                event_id=event_id,
                volunteer_id=v.id,
                magic_token=create_volunteer_token(),
            )
            db.add(ev)
            added += 1
    db.commit()
    return {"attached": added}


@router.post("/{event_id}/send-invites")
def send_invites(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> dict:
    """No-op: invite flow is now link-based; admin shares the event join link."""
    get_admin_event_or_404(db, event_id, require_active=True)
    evs = db.query(EventVolunteer).filter(EventVolunteer.event_id == event_id).all()
    return {"sent": 0, "total": len(evs)}


@router.get("/{event_id}/export-excel")
def export_event_excel(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
):
    event = get_admin_event_or_404(db, event_id)
    residents = db.query(Resident).filter(Resident.event_id == event_id).all()
    log_rows = (
        db.query(EventLog)
        .filter(EventLog.event_id == event_id)
        .order_by(EventLog.created_at.asc())
        .all()
    )
    volunteer_ids = [row.author_volunteer_id for row in log_rows if row.author_volunteer_id]
    volunteers = (
        db.query(Volunteer).filter(Volunteer.id.in_(volunteer_ids)).all()
        if volunteer_ids
        else []
    )
    volunteer_names = {
        volunteer.id: f"{volunteer.first_name} {volunteer.last_name}".strip()
        or volunteer.first_name
        or "מתנדב"
        for volunteer in volunteers
    }
    log_entries = [
        {
            "created_at": row.created_at,
            "author_type": row.author_type.value,
            "author_name": (
                volunteer_names.get(row.author_volunteer_id) or "מתנדב"
                if row.author_volunteer_id
                else "מנהל"
            ),
            "message": row.message,
        }
        for row in log_rows
    ]
    buffer = export_event_to_excel(event, residents, log_entries)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=event-{event_id}.xlsx"},
    )


@router.get("/{event_id}/residents", response_model=List[ResidentListRow])
def list_event_residents(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> List[ResidentListRow]:
    get_admin_event_or_404(db, event_id)
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
    current_user: AdminAuth = Depends(get_current_user),
) -> List[EventVolunteerRow]:
    get_admin_event_or_404(db, event_id)
    evs = (
        db.query(EventVolunteer, Volunteer)
        .join(Volunteer, EventVolunteer.volunteer_id == Volunteer.id)
        .filter(
            EventVolunteer.event_id == event_id,
        )
        .all()
    )
    return [
        EventVolunteerRow(
            id=ev.id,
            volunteer_id=ev.volunteer_id,
            volunteer_name=f"{v.first_name} {v.last_name}".strip() or v.first_name,
            volunteer_phone=v.phone,
            magic_token=ev.magic_token,
            status=ev.status.value if ev.status else None,
            updated_at=ev.updated_at,
        )
        for ev, v in evs
    ]


@router.get("/{event_id}/log", response_model=List[EventLogRow])
def list_event_log(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> List[EventLogRow]:
    get_admin_event_or_404(db, event_id)
    rows = (
        db.query(EventLog)
        .filter(EventLog.event_id == event_id)
        .order_by(EventLog.created_at.asc())
        .all()
    )
    volunteer_ids = [r.author_volunteer_id for r in rows if r.author_volunteer_id]
    volunteers = (
        db.query(Volunteer).filter(Volunteer.id.in_(volunteer_ids)).all()
        if volunteer_ids
        else []
    )
    vol_names = {
        v.id: f"{v.first_name} {v.last_name}".strip() or v.first_name
        for v in volunteers
    }
    result = []
    for r in rows:
        if r.author_volunteer_id:
            author_name = vol_names.get(r.author_volunteer_id) or "מתנדב"
        else:
            author_name = "מנהל"
        result.append(
            EventLogRow(
                id=r.id,
                message=r.message,
                author_type=r.author_type.value,
                author_name=author_name,
                created_at=r.created_at,
            )
        )
    return result


@router.post(
    "/{event_id}/log", response_model=EventLogRow, status_code=status.HTTP_201_CREATED
)
def add_event_log(
    event_id: int,
    body: EventLogCreate,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> EventLogRow:
    get_admin_event_or_404(db, event_id, require_active=True)
    log = EventLog(
        event_id=event_id,
        message=body.message,
        author_type=EventLogAuthorType.ADMIN,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    broadcast_event_updated_sync(event_id)
    return EventLogRow(
        id=log.id,
        message=log.message,
        author_type=log.author_type.value,
        author_name="מנהל",
        created_at=log.created_at,
    )
