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


@dataclass(frozen=True)
class DailyReviewData:
    date: str
    daily_summary: str
    valid_session_count: int
    main_topics: list
    frequent_objections: list
    overall_strengths: list
    overall_weaknesses: list
    top_improvement: dict
    best_phrase_today: str
    phrase_to_replace: dict
    priority_follow_ups: list
    tomorrow_focus: list
    raw_payload: dict | None = None


class ASRAdapter(Protocol):
    def transcribe(
        self, session: AudioSession, hotwords: list[str] | None = None
    ) -> list[TranscriptSegmentData]:
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


class DailyReviewAdapter(Protocol):
    def summarize_daily_review(self, payload: dict) -> DailyReviewData:
        """Return structured coaching summary for aggregated daily review data."""
