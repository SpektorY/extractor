from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Volunteer
from app.schemas.volunteer import VolunteerCreate, VolunteerUpdate, VolunteerResponse
from app.api.v1.endpoints.auth import get_current_user, AdminAuth

router = APIRouter()


@router.get("", response_model=List[VolunteerResponse])
def list_volunteers(
    group_tag: Optional[str] = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> List[VolunteerResponse]:
    q = db.query(Volunteer)
    if not include_deleted:
        q = q.filter(Volunteer.deleted_at.is_(None))
    if group_tag:
        q = q.filter(Volunteer.group_tag == group_tag)
    volunteers = q.order_by(Volunteer.last_name, Volunteer.first_name).all()
    return [VolunteerResponse.model_validate(v) for v in volunteers]


@router.post("", response_model=VolunteerResponse, status_code=status.HTTP_201_CREATED)
def create_volunteer(
    body: VolunteerCreate,
    db: Session = Depends(get_db),
    current_user: AdminAuth = Depends(get_current_user),
) -> VolunteerResponse:
    existing = db.query(Volunteer).filter(
        Volunteer.phone == body.phone,
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
        phone=body.phone,
        group_tag=body.group_tag,
        living_area=body.living_area,
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    return VolunteerResponse.model_validate(volunteer)


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
        existing = db.query(Volunteer).filter(
            Volunteer.phone == body.phone,
            Volunteer.deleted_at.is_(None),
            Volunteer.id != volunteer_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="טלפון זה כבר רשום במערכת",
            )
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
    from datetime import datetime, timezone
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
    db.commit()
    db.refresh(v)
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
    # Unique placeholder so we don't violate volunteers.phone unique constraint
    v.phone = f"anon-{v.id}"
    v.group_tag = None
    v.living_area = None
    v.anonymized = True
    v.deleted_at = None  # keep record for history but anonymized
    db.commit()
    return None
