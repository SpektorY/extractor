from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Volunteer, VolunteerStatus
from app.schemas.volunteer import VolunteerResponse
from app.schemas.volunteer_signup import VolunteerSignupCreate

router = APIRouter()


@router.post("/volunteer-signup", response_model=VolunteerResponse, status_code=status.HTTP_201_CREATED)
def volunteer_signup(body: VolunteerSignupCreate, db: Session = Depends(get_db)) -> VolunteerResponse:
    """Public self-signup: adds a volunteer with status PENDING until admin approves."""
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
        last_name=body.last_name or "",
        phone=body.phone,
        group_tag=body.group_tag,
        living_area=body.area,
        status=VolunteerStatus.PENDING,
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    return VolunteerResponse.model_validate(volunteer)
