from dataclasses import dataclass
from typing import Protocol

from app.models import AudioSession


@dataclass(frozen=True)
class TranscriptSegmentData:
    start_ms: int
    end_ms: int
    speaker_id: str | None
    speaker_label: str | None
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class AnalysisData:
    summary: str
    scores: dict
    strengths: list
    weaknesses: list
    todos: list
    better_phrases: list
    raw_payload: dict | None = None


class ASRAdapter(Protocol):
    def transcribe(self, session: AudioSession) -> list[TranscriptSegmentData]:
        """Return normalized transcript segments for an uploaded audio session."""


class DiarizationAdapter(Protocol):
    def assign_speakers(
        self, segments: list[TranscriptSegmentData]
    ) -> list[TranscriptSegmentData]:
        """Return transcript segments with speaker labels normalized."""


class AnalysisAdapter(Protocol):
    def analyze(
        self, session: AudioSession, segments: list[TranscriptSegmentData]
    ) -> AnalysisData:
        """Return structured communication analysis for transcript segments."""
