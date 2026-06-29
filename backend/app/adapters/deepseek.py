import json
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.adapters.base import AnalysisData, TranscriptSegmentData
from app.config import Settings
from app.models import AudioSession

SYSTEM_PROMPT = (
    "你是一个中文业务沟通教练。你只根据带说话人和时间戳的谈话转写分析用户"
    "在业务沟通中的表现。输出必须是合法 JSON，不要输出 Markdown 或解释文字。"
)

USER_ROLE_CONTEXT = (
    "用户是一名财险产品与渠道销售管理者，沟通需要清楚目标、压实责任、"
    "明确时间点和交付物，并处理费用政策、流程、产品支持和资源不足等异议。"
)

REPAIR_PROMPT = (
    "你刚才的输出不是合法 JSON。请只输出合法 JSON，不要 Markdown，不要解释，"
    "保持原有字段结构并修复格式错误。"
)


class ScorePayload(BaseModel):
    goal_clarity: int = Field(ge=0, le=10)
    question_quality: int = Field(ge=0, le=10)
    business_actionability: int = Field(ge=0, le=10)
    responsibility_closure: int = Field(ge=0, le=10)
    objection_handling: int = Field(ge=0, le=10)
    rhythm_control: int = Field(ge=0, le=10)
    expression_efficiency: int = Field(ge=0, le=10)
    follow_up_closure: int = Field(ge=0, le=10)


class AnalysisPayload(BaseModel):
    summary: str
    scores: ScorePayload
    strengths: list[Any] = Field(default_factory=list)
    weaknesses: list[Any] = Field(default_factory=list)
    todos: list[Any] = Field(default_factory=list)
    better_phrases: list[Any] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class DeepSeekAnalysisAdapter:
    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.settings = settings
        self.client = client or httpx.Client(timeout=60)

    def analyze(
        self, session: AudioSession, segments: list[TranscriptSegmentData]
    ) -> AnalysisData:
        first_content = self._chat(self._build_user_prompt(session, segments))
        try:
            payload = self._validate_json(first_content)
        except (json.JSONDecodeError, ValidationError):
            payload = self._validate_json(self._chat(REPAIR_PROMPT))
        return AnalysisData(
            summary=payload.summary,
            scores=payload.scores.model_dump(),
            strengths=payload.strengths,
            weaknesses=payload.weaknesses,
            todos=payload.todos,
            better_phrases=payload.better_phrases,
            raw_payload=payload.model_dump(),
        )

    def _chat(self, user_prompt: str) -> str:
        response = self.client.post(
            self._chat_completions_url(),
            headers={"Authorization": f"Bearer {self.settings.deepseek_api_key}"},
            json={
                "model": self.settings.deepseek_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        body = response.json()
        return body["choices"][0]["message"]["content"]

    def _chat_completions_url(self) -> str:
        return f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions"

    def _validate_json(self, content: str) -> AnalysisPayload:
        return AnalysisPayload.model_validate(json.loads(content))

    def _build_user_prompt(
        self, session: AudioSession, segments: list[TranscriptSegmentData]
    ) -> str:
        session_metadata = {
            "session_id": session.id,
            "scene": session.scene,
            "privacy_level": session.privacy_level,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat(),
        }
        transcript_segments = [
            {
                "start_ms": segment.start_ms,
                "end_ms": segment.end_ms,
                "speaker_id": segment.speaker_id,
                "speaker_label": segment.speaker_label,
                "text": segment.text,
                "confidence": segment.confidence,
            }
            for segment in segments
        ]
        return (
            "请分析以下业务沟通记录，并严格输出 JSON。\n\n"
            f"用户角色背景：\n{USER_ROLE_CONTEXT}\n\n"
            f"会话信息：\n{json.dumps(session_metadata, ensure_ascii=False)}\n\n"
            f"转写内容：\n{json.dumps(transcript_segments, ensure_ascii=False)}\n\n"
            "JSON 必须包含 summary、scores、strengths、weaknesses、todos、better_phrases。"
        )


def build_analysis_adapter(settings: Settings):
    if settings.use_deepseek and settings.deepseek_api_key:
        return DeepSeekAnalysisAdapter(settings)
    from app.adapters.mock import MockAnalysisAdapter

    return MockAnalysisAdapter()
