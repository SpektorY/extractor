from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import AdminAuth, get_current_user
from app.core.database import get_db
from app.models import Volunteer, VolunteerStatus
from app.schemas.volunteer import VolunteerCreate, VolunteerResponse, VolunteerUpdate
from app.services.excel_import import parse_volunteers_file
from app.services.sms import normalize_phone_for_storage, send_approved_sms

router = APIRouter()


class VolunteerImportResult(BaseModel):
    imported: int
    errors: List[str]


def _normalize_phone_or_400(phone: str) -> str:
    try:
        return normalize_phone_for_storage(phone)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=List[VolunteerResponse])
def list_volunteers(
    group_tag: Optional[str] = None,
    status: Optional[VolunteerStatus] = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> List[VolunteerResponse]:
    q = db.query(Volunteer)
    if not include_deleted:
        q = q.filter(Volunteer.deleted_at.is_(None))
    if group_tag:
        q = q.filter(Volunteer.group_tag == group_tag)
    if status:
        q = q.filter(Volunteer.status == status)
    volunteers = q.order_by(Volunteer.last_name, Volunteer.first_name).all()
    return [VolunteerResponse.model_validate(v) for v in volunteers]


@router.post("", response_model=VolunteerResponse, status_code=status.HTTP_201_CREATED)
def create_volunteer(
    body: VolunteerCreate,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> VolunteerResponse:
    normalized_phone = _normalize_phone_or_400(body.phone)
    existing = db.query(Volunteer).filter(
        Volunteer.phone == normalized_phone,
        Volunteer.deleted_at.is_(None),
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="טלפון זה כבר רשום במערכת",
        )
    volunteer = Volunteer(
        first_name=body.first_name,
        last_name=body.last_name,
        phone=normalized_phone,
        group_tag=body.group_tag,
        living_area=body.living_area,
        status=VolunteerStatus.APPROVED,
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    return VolunteerResponse.model_validate(volunteer)


@router.post("/import", response_model=VolunteerImportResult)
def import_volunteers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> VolunteerImportResult:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="לא נבחר קובץ")
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="הקובץ ריק")
    rows, errors = parse_volunteers_file(content, file.filename)
    imported = 0
    for idx, row in enumerate(rows, start=2):
        try:
            normalized_phone = normalize_phone_for_storage(row.phone)
        except ValueError as exc:
            errors.append(f"שורה {idx}: {exc}")
            continue
        existing = (
            db.query(Volunteer)
            .filter(Volunteer.phone == normalized_phone, Volunteer.deleted_at.is_(None))
            .first()
        )
        if existing:
            errors.append(f"שורה {idx}: טלפון זה כבר רשום במערכת")
            continue
        volunteer = Volunteer(
            first_name=row.first_name,
            last_name=row.last_name,
            phone=normalized_phone,
            group_tag=row.group_tag,
            living_area=row.living_area,
            status=VolunteerStatus.APPROVED,
        )
        db.add(volunteer)
        imported += 1
    db.commit()
    return VolunteerImportResult(imported=imported, errors=errors)


@router.get("/{volunteer_id}", response_model=VolunteerResponse)
def get_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> VolunteerResponse:
    v = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="מתנדב לא נמצא")
    return VolunteerResponse.model_validate(v)


@router.patch("/{volunteer_id}", response_model=VolunteerResponse)
def update_volunteer(
    volunteer_id: int,
    body: VolunteerUpdate,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> VolunteerResponse:
    v = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="מתנדב לא נמצא")
    if v.anonymized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="מתנדב זה עבר אנונימיזציה")
    if body.phone is not None and body.phone != v.phone:
        normalized_phone = _normalize_phone_or_400(body.phone)
        existing = db.query(Volunteer).filter(
            Volunteer.phone == normalized_phone,
            Volunteer.deleted_at.is_(None),
            Volunteer.id != volunteer_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="טלפון זה כבר רשום במערכת",
            )
        body.phone = normalized_phone
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(v, key, value)
    db.commit()
    db.refresh(v)
    return VolunteerResponse.model_validate(v)


@router.delete("/{volunteer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> None:
    v = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="מתנדב לא נמצא")
    v.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return None


@router.post("/{volunteer_id}/approve", response_model=VolunteerResponse)
def approve_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> VolunteerResponse:
    v = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="מתנדב לא נמצא")
    if v.anonymized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="מתנדב זה עבר אנונימיזציה")
    v.status = VolunteerStatus.APPROVED
    db.commit()
    db.refresh(v)
    send_approved_sms(v.phone)
    return VolunteerResponse.model_validate(v)


@router.post("/{volunteer_id}/anonymize", status_code=status.HTTP_204_NO_CONTENT)
def anonymize_volunteer(
    volunteer_id: int,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> None:
    v = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="מתנדב לא נמצא")
    v.first_name = "אנונימי"
    v.last_name = ""
    v.phone = f"anon-{v.id}"
    v.group_tag = None
    v.living_area = None
    v.anonymized = True
    v.deleted_at = None
    db.commit()
    return None
