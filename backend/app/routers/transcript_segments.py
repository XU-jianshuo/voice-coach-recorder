from fastapi import APIRouter, Depends
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import http_error
from app.models import TranscriptSegment
from app.schemas import SpeakerLabelUpdate, SpeakerLabelUpdateResponse
from app.security import require_device_token

router = APIRouter(
    prefix="/transcript-segments",
    dependencies=[Depends(require_device_token)],
)


@router.patch("/{segment_id}/speaker", response_model=SpeakerLabelUpdateResponse)
def update_speaker_label(
    segment_id: int,
    payload: SpeakerLabelUpdate,
    db: Session = Depends(get_db),
) -> SpeakerLabelUpdateResponse:
    segment = db.get(TranscriptSegment, segment_id)
    if segment is None:
        raise http_error(404, "segment_not_found", "Transcript segment was not found")

    original_speaker_id = segment.speaker_id
    segment.speaker_label = payload.speaker_label
    if payload.speaker_profile_id:
        segment.speaker_id = payload.speaker_profile_id

    if payload.apply_to_session:
        stmt = (
            update(TranscriptSegment)
            .where(TranscriptSegment.session_id == segment.session_id)
            .where(TranscriptSegment.speaker_id == original_speaker_id)
            .values(
                speaker_label=payload.speaker_label,
                speaker_id=payload.speaker_profile_id or original_speaker_id,
            )
        )
        db.execute(stmt)

    db.add(segment)
    db.commit()
    return SpeakerLabelUpdateResponse(
        segment_id=segment.id,
        speaker_label=segment.speaker_label,
        updated=True,
    )
