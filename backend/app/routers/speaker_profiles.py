from uuid import uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import SpeakerProfile
from app.schemas import (
    SpeakerProfileCreate,
    SpeakerProfileListResponse,
    SpeakerProfileResponse,
)
from app.security import require_device_token

router = APIRouter(
    prefix="/speaker-profiles",
    dependencies=[Depends(require_device_token)],
)


@router.get("", response_model=SpeakerProfileListResponse)
def list_speaker_profiles(db: Session = Depends(get_db)) -> SpeakerProfileListResponse:
    profiles = db.scalars(select(SpeakerProfile).order_by(SpeakerProfile.created_at)).all()
    return SpeakerProfileListResponse(items=profiles)


@router.post(
    "",
    response_model=SpeakerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_speaker_profile(
    payload: SpeakerProfileCreate, db: Session = Depends(get_db)
) -> SpeakerProfile:
    profile = SpeakerProfile(
        id=f"speaker_{uuid4().hex[:12]}",
        display_name=payload.display_name,
        type=payload.type,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
