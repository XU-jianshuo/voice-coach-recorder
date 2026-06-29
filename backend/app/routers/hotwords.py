from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import http_error
from app.models import Hotword
from app.schemas import HotwordCreate, HotwordListResponse, HotwordResponse
from app.security import require_device_token
from app.services.hotwords import seed_default_hotwords

router = APIRouter(
    prefix="/hotwords",
    dependencies=[Depends(require_device_token)],
)


@router.get("", response_model=HotwordListResponse)
def list_hotwords(db: Session = Depends(get_db)) -> HotwordListResponse:
    seed_default_hotwords(db)
    hotwords = db.scalars(select(Hotword).order_by(Hotword.id)).all()
    return HotwordListResponse(items=hotwords)


@router.post("", response_model=HotwordResponse, status_code=status.HTTP_201_CREATED)
def create_hotword(payload: HotwordCreate, db: Session = Depends(get_db)) -> Hotword:
    hotword = Hotword(
        text=payload.text,
        category=payload.category,
        weight=payload.weight,
    )
    db.add(hotword)
    db.commit()
    db.refresh(hotword)
    return hotword


@router.delete("/{hotword_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hotword(hotword_id: int, db: Session = Depends(get_db)) -> Response:
    hotword = db.get(Hotword, hotword_id)
    if hotword is None:
        raise http_error(404, "hotword_not_found", "Hotword was not found")
    db.delete(hotword)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
