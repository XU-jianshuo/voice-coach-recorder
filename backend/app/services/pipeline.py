from sqlalchemy.orm import Session, sessionmaker

from app.adapters.base import AnalysisAdapter, ASRAdapter, DiarizationAdapter
from app.adapters.deepseek import build_analysis_adapter
from app.adapters.mock import MockAnalysisAdapter, MockASRAdapter, NoOpDiarizationAdapter
from app.config import Settings
from app.db import create_engine_for
from app.models import (
    AudioSession,
    CommunicationAnalysis,
    SessionStatus,
    TranscriptSegment,
    Hotword,
)


class ProcessingPipeline:
    def __init__(
        self,
        db: Session,
        asr_adapter: ASRAdapter | None = None,
        diarization_adapter: DiarizationAdapter | None = None,
        analysis_adapter: AnalysisAdapter | None = None,
        settings: Settings | None = None,
    ):
        self.db = db
        self.asr_adapter = asr_adapter or MockASRAdapter()
        self.diarization_adapter = diarization_adapter or NoOpDiarizationAdapter()
        self.analysis_adapter = analysis_adapter or (
            build_analysis_adapter(settings) if settings else MockAnalysisAdapter()
        )

    def process(self, session_id: str) -> AudioSession:
        session = self.db.get(AudioSession, session_id)
        if session is None:
            raise ValueError(f"Audio session not found: {session_id}")

        try:
            self._set_status(session, SessionStatus.transcribing)
            hotwords = [hotword.text for hotword in self.db.query(Hotword).all()]
            asr_segments = self.asr_adapter.transcribe(session, hotwords=hotwords)
            segments = self.diarization_adapter.assign_speakers(asr_segments)
            for segment in segments:
                self.db.add(
                    TranscriptSegment(
                        session_id=session.id,
                        start_ms=segment.start_ms,
                        end_ms=segment.end_ms,
                        speaker_id=segment.speaker_id,
                        speaker_label=segment.speaker_label,
                        text=segment.text,
                        confidence=segment.confidence,
                    )
                )
            self._set_status(session, SessionStatus.transcribed)

            self._set_status(session, SessionStatus.analyzing)
            analysis = self.analysis_adapter.analyze(session, segments)
            self.db.add(
                CommunicationAnalysis(
                    session_id=session.id,
                    summary=analysis.summary,
                    scores=analysis.scores,
                    strengths=analysis.strengths,
                    weaknesses=analysis.weaknesses,
                    todos=analysis.todos,
                    better_phrases=analysis.better_phrases,
                    raw_payload=analysis.raw_payload,
                )
            )
            self._set_status(session, SessionStatus.analyzed)
        except Exception:
            self.db.rollback()
            failed_session = self.db.get(AudioSession, session_id)
            if failed_session is not None:
                failed_session.status = SessionStatus.failed.value
                self.db.commit()
            raise

        self.db.refresh(session)
        return session

    def _set_status(self, session: AudioSession, status: SessionStatus) -> None:
        session.status = status.value
        self.db.add(session)
        self.db.commit()


def process_audio_session(session_id: str, settings: Settings) -> None:
    engine = create_engine_for(settings)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_local()
    try:
        ProcessingPipeline(db, settings=settings).process(session_id)
    finally:
        db.close()
