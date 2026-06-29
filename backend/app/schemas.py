from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class SpeakerProfileCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    type: Literal["self", "known", "unknown"]


class SpeakerProfileResponse(BaseModel):
    id: str
    display_name: str
    type: str
    voiceprint_path: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SpeakerProfileListResponse(BaseModel):
    items: list[SpeakerProfileResponse]


class SpeakerLabelUpdate(BaseModel):
    speaker_label: str = Field(min_length=1, max_length=120)
    speaker_profile_id: str | None = None
    apply_to_session: bool = False


class SpeakerLabelUpdateResponse(BaseModel):
    segment_id: int
    speaker_label: str
    updated: bool


class HotwordCreate(BaseModel):
    text: str = Field(min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=120)
    weight: int = Field(default=10, ge=1, le=100)


class HotwordResponse(BaseModel):
    id: int
    text: str
    category: str | None = None
    weight: int

    model_config = ConfigDict(from_attributes=True)


class HotwordListResponse(BaseModel):
    items: list[HotwordResponse]
