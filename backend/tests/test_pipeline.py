from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.adapters.base import TranscriptSegmentData
from app.db import Base, create_engine_for
from app.models import AudioSession, SessionStatus
from app.services.pipeline import ProcessingPipeline


class FailingASRAdapter:
    def transcribe(
        self, session: AudioSession, hotwords: list[str] | None = None
    ) -> list[TranscriptSegmentData]:
        raise RuntimeError("mock ASR failure")


def test_pipeline_marks_session_failed_when_adapter_raises(test_settings):
    engine = create_engine_for(test_settings)
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_local()
    try:
        audio_session = AudioSession(
            id="session_failure",
            device_id="android_test",
            started_at=datetime(2026, 6, 25, 9, 30, tzinfo=timezone.utc),
            ended_at=datetime(2026, 6, 25, 9, 32, tzinfo=timezone.utc),
            status=SessionStatus.queued.value,
            audio_path="audio/test.m4a",
        )
        db.add(audio_session)
        db.commit()

        pipeline = ProcessingPipeline(db, asr_adapter=FailingASRAdapter())
        try:
            pipeline.process(audio_session.id)
        except RuntimeError:
            pass

        db.refresh(audio_session)
        assert audio_session.status == SessionStatus.failed.value
    finally:
        db.close()
