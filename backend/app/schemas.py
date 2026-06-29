from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    app: str


class AudioSessionCreateResponse(BaseModel):
    session_id: str
    status: str


class AudioSessionResponse(BaseModel):
    id: str
    device_id: str
    started_at: datetime
    ended_at: datetime
    status: str
    scene: str | None = None
    privacy_level: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TranscriptSegmentResponse(BaseModel):
    id: int
    start_ms: int
    end_ms: int
    speaker_id: str | None = None
    speaker_label: str | None = None
    text: str
    confidence: float | None = None

    model_config = ConfigDict(from_attributes=True)


class TranscriptResponse(BaseModel):
    session_id: str
    segments: list[TranscriptSegmentResponse]


class AnalysisResponse(BaseModel):
    session_id: str
    summary: str
    scores: dict
    strengths: list
    weaknesses: list
    todos: list
    better_phrases: list

    model_config = ConfigDict(from_attributes=True)
