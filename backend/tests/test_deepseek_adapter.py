import json
from datetime import datetime, timezone

import httpx

from app.adapters.base import TranscriptSegmentData
from app.adapters.deepseek import DeepSeekAnalysisAdapter, build_analysis_adapter
from app.adapters.mock import MockAnalysisAdapter
from app.config import Settings
from app.models import AudioSession


def make_session() -> AudioSession:
    return AudioSession(
        id="session_deepseek",
        device_id="android_test",
        started_at=datetime(2026, 6, 25, 9, 30, tzinfo=timezone.utc),
        ended_at=datetime(2026, 6, 25, 9, 32, tzinfo=timezone.utc),
        audio_path="audio/test.m4a",
        status="transcribed",
        scene="channel",
        privacy_level="work",
    )


def make_segments() -> list[TranscriptSegmentData]:
    return [
        TranscriptSegmentData(
            start_ms=0,
            end_ms=1200,
            speaker_id="speaker_me",
            speaker_label="我",
            text="今天先确认续保推进清单。",
            confidence=0.95,
        )
    ]


def make_openai_response(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": content}}]},
    )


def test_deepseek_adapter_returns_validated_analysis_from_json_response():
    calls = []
    valid_content = json.dumps(
        {
            "summary": "DeepSeek mock summary",
            "scores": {
                "goal_clarity": 8,
                "question_quality": 7,
                "business_actionability": 8,
                "responsibility_closure": 7,
                "objection_handling": 7,
                "rhythm_control": 8,
                "expression_efficiency": 8,
                "follow_up_closure": 7,
            },
            "strengths": ["目标清楚"],
            "weaknesses": ["责任人还可更明确"],
            "todos": [{"owner": "我", "task": "确认清单", "due_date": "2026-06-26"}],
            "better_phrases": [{"original": "推进一下", "improved": "明天下午给第一版"}],
        },
        ensure_ascii=False,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "deepseek-chat"
        assert payload["response_format"] == {"type": "json_object"}
        assert "test-key" not in request.content.decode()
        return make_openai_response(valid_content)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = DeepSeekAnalysisAdapter(
        Settings(
            use_deepseek=True,
            deepseek_api_key="test-key",
            deepseek_base_url="https://deepseek.example",
            deepseek_model="deepseek-chat",
        ),
        client=client,
    )

    analysis = adapter.analyze(make_session(), make_segments())

    assert len(calls) == 1
    assert analysis.summary == "DeepSeek mock summary"
    assert analysis.scores["goal_clarity"] == 8
    assert analysis.todos[0]["task"] == "确认清单"


def test_deepseek_adapter_repairs_invalid_json_once():
    responses = iter(
        [
            make_openai_response("not json"),
            make_openai_response(
                json.dumps(
                    {
                        "summary": "Repaired summary",
                        "scores": {
                            "goal_clarity": 8,
                            "question_quality": 7,
                            "business_actionability": 8,
                            "responsibility_closure": 7,
                            "objection_handling": 7,
                            "rhythm_control": 8,
                            "expression_efficiency": 8,
                            "follow_up_closure": 7,
                        },
                        "strengths": [],
                        "weaknesses": [],
                        "todos": [],
                        "better_phrases": [],
                    },
                    ensure_ascii=False,
                )
            ),
        ]
    )
    prompts = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        prompts.append(payload["messages"][-1]["content"])
        return next(responses)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = DeepSeekAnalysisAdapter(
        Settings(
            use_deepseek=True,
            deepseek_api_key="test-key",
            deepseek_base_url="https://deepseek.example",
            deepseek_model="deepseek-chat",
        ),
        client=client,
    )

    analysis = adapter.analyze(make_session(), make_segments())

    assert analysis.summary == "Repaired summary"
    assert len(prompts) == 2
    assert "JSON" in prompts[1]


def test_analysis_adapter_falls_back_to_mock_without_api_key():
    adapter = build_analysis_adapter(Settings(use_deepseek=True, deepseek_api_key=""))

    assert isinstance(adapter, MockAnalysisAdapter)
