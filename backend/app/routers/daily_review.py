from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.schemas import DailyReviewResponse
from app.security import require_device_token
from app.services.daily_review import build_daily_review

router = APIRouter(
    prefix="/daily-review",
    dependencies=[Depends(require_device_token)],
)


@router.get("", response_model=DailyReviewResponse)
def get_daily_review(
    date: date = Query(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DailyReviewResponse:
    return build_daily_review(db, date.isoformat(), settings)
