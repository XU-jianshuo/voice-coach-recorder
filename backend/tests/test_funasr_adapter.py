from datetime import datetime, timezone

import pytest

from app.adapters.funasr import FunASRAdapter, FunASRUnavailableError
from app.adapters.mock import MockASRAdapter
from app.config import Settings
from app.models import AudioSession
from app.services.pipeline import build_asr_adapter


def make_session() -> AudioSession:
    return AudioSession(
        id="session_funasr",
        device_id="android_test",
        started_at=datetime(2026, 6, 25, 9, 30, tzinfo=timezone.utc),
        ended_at=datetime(2026, 6, 25, 9, 32, tzinfo=timezone.utc),
        audio_path="audio/test.m4a",
        status="queued",
    )


def test_build_asr_adapter_defaults_to_mock_provider():
    adapter = build_asr_adapter(Settings(asr_provider="mock"))

    assert isinstance(adapter, MockASRAdapter)


def test_build_asr_adapter_supports_funasr_provider():
    adapter = build_asr_adapter(Settings(asr_provider="funasr"))

    assert isinstance(adapter, FunASRAdapter)


def test_funasr_adapter_fails_clearly_when_dependency_is_missing():
    adapter = FunASRAdapter(Settings(asr_provider="funasr"))

    with pytest.raises(FunASRUnavailableError, match="FunASR dependencies"):
        adapter.transcribe(make_session(), hotwords=["车险", "续保率"])
