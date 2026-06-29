import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.errors import http_error
from app.models import AudioSession, CommunicationAnalysis, SessionStatus
from app.schemas import (
    AnalysisResponse,
    AudioSessionCreateResponse,
    AudioSessionResponse,
    TranscriptResponse,
)
from app.security import require_device_token
from app.services.pipeline import process_audio_session
from app.services.storage import AudioStorage

router = APIRouter(
    prefix="/audio-sessions",
    dependencies=[Depends(require_device_token)],
)


def build_session_id(started_at: datetime) -> str:
    return f"session_{started_at.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"


def parse_metadata(metadata: str | None) -> dict:
    if not metadata:
        return {}
    try:
        parsed = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise http_error(400, "invalid_metadata", "metadata must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise http_error(400, "invalid_metadata", "metadata must be a JSON object")
    return parsed


@router.post(
    "",
    response_model=AudioSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_audio_session(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    device_id: str = Form(...),
    started_at: datetime = Form(...),
    ended_at: datetime = Form(...),
    metadata: str | None = Form(None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AudioSessionCreateResponse:
    metadata_dict = parse_metadata(metadata)
    session_id = build_session_id(started_at)
    storage = AudioStorage(settings.storage_dir)
    audio_path = storage.save_upload(audio, session_id, started_at)

    session = AudioSession(
        id=session_id,
        device_id=device_id,
        started_at=started_at,
        ended_at=ended_at,
        status=SessionStatus.queued.value,
        audio_path=audio_path,
        scene=metadata_dict.get("scene"),
        privacy_level=metadata_dict.get("privacy_level"),
        session_metadata=metadata_dict,
    )
    db.add(session)
    db.commit()
    background_tasks.add_task(process_audio_session, session_id, settings)

    return AudioSessionCreateResponse(session_id=session_id, status=session.status)


@router.get("/{session_id}", response_model=AudioSessionResponse)
def get_audio_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> AudioSession:
    session = db.get(AudioSession, session_id)
    if session is None:
        raise http_error(404, "session_not_found", "Audio session was not found")
    return session


@router.get("/{session_id}/transcript", response_model=TranscriptResponse)
def get_transcript(
    session_id: str,
    db: Session = Depends(get_db),
) -> TranscriptResponse:
    session = db.get(AudioSession, session_id)
    if session is None:
        raise http_error(404, "session_not_found", "Audio session was not found")
    return TranscriptResponse(session_id=session_id, segments=session.transcript_segments)


@router.get("/{session_id}/analysis", response_model=AnalysisResponse)
def get_analysis(
    session_id: str,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    session = db.get(AudioSession, session_id)
    if session is None:
        raise http_error(404, "session_not_found", "Audio session was not found")

    analysis = db.scalar(
        select(CommunicationAnalysis).where(
            CommunicationAnalysis.session_id == session_id
        )
    )
    if analysis is None:
        raise http_error(404, "analysis_not_found", "Analysis is not available yet")

    return AnalysisResponse(
        session_id=session_id,
        summary=analysis.summary,
        scores=analysis.scores,
        strengths=analysis.strengths,
        weaknesses=analysis.weaknesses,
        todos=analysis.todos,
        better_phrases=analysis.better_phrases,
    )
