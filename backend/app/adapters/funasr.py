from collections.abc import Iterable
from typing import Any

from app.adapters.base import TranscriptSegmentData
from app.config import Settings
from app.models import AudioSession


class FunASRUnavailableError(RuntimeError):
    """Raised when optional FunASR dependencies or model files are unavailable."""


class FunASRAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._model: Any | None = None

    def transcribe(
        self, session: AudioSession, hotwords: list[str] | None = None
    ) -> list[TranscriptSegmentData]:
        model = self._load_model()
        result = model.generate(
            input=session.audio_path,
            hotword=" ".join(hotwords or []),
            vad_kwargs=self._vad_options(),
            punc_kwargs=self._punctuation_options(),
            timestamp=True,
            return_raw_text=False,
        )
        return self._normalize_segments(result)

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from funasr import AutoModel
        except ImportError as exc:
            raise FunASRUnavailableError(
                "FunASR dependencies are not installed. Install optional FunASR/SenseVoice "
                "packages in a model runtime, or set ASR_PROVIDER=mock for local development."
            ) from exc

        model_path = self.settings.funasr_model_dir
        if not model_path:
            raise FunASRUnavailableError(
                "FUNASR_MODEL_DIR is not configured. Set it to a local FunASR/SenseVoice model path."
            )
        try:
            self._model = AutoModel(model=model_path)
        except Exception as exc:
            raise FunASRUnavailableError(
                "FunASR model could not be loaded. Check FUNASR_MODEL_DIR, model files, "
                "and runtime dependencies."
            ) from exc
        return self._model

    def _vad_options(self) -> dict[str, Any]:
        return {"enabled": True}

    def _punctuation_options(self) -> dict[str, Any]:
        return {"enabled": True}

    def diarize(self, result: Any) -> Any:
        """Placeholder for CAM++ or compatible diarization integration."""
        return result

    def _normalize_segments(self, result: Any) -> list[TranscriptSegmentData]:
        normalized: list[TranscriptSegmentData] = []
        for index, item in enumerate(self._iter_result_items(result)):
            text = str(item.get("text") or item.get("sentence") or "").strip()
            if not text:
                continue
            start_ms, end_ms = self._extract_timestamps(item, index)
            speaker_index = item.get("speaker") or item.get("spk") or item.get("speaker_id")
            if speaker_index is None:
                speaker_index = 0
            speaker_label = self._normalize_speaker_label(speaker_index)
            normalized.append(
                TranscriptSegmentData(
                    start_ms=start_ms,
                    end_ms=end_ms,
                    speaker_id=f"speaker_{speaker_index}",
                    speaker_label=speaker_label,
                    text=text,
                    confidence=self._extract_confidence(item),
                )
            )
        return normalized

    def _iter_result_items(self, result: Any) -> Iterable[dict[str, Any]]:
        if isinstance(result, dict):
            if isinstance(result.get("sentence_info"), list):
                return result["sentence_info"]
            if isinstance(result.get("segments"), list):
                return result["segments"]
            return [result]
        if isinstance(result, list):
            items: list[dict[str, Any]] = []
            for entry in result:
                if isinstance(entry, dict) and isinstance(entry.get("sentence_info"), list):
                    items.extend(entry["sentence_info"])
                elif isinstance(entry, dict) and isinstance(entry.get("segments"), list):
                    items.extend(entry["segments"])
                elif isinstance(entry, dict):
                    items.append(entry)
            return items
        return []

    def _extract_timestamps(self, item: dict[str, Any], index: int) -> tuple[int, int]:
        start = item.get("start") or item.get("start_ms")
        end = item.get("end") or item.get("end_ms")
        if isinstance(item.get("timestamp"), list) and item["timestamp"]:
            first = item["timestamp"][0]
            last = item["timestamp"][-1]
            if isinstance(first, list) and len(first) >= 2:
                start = first[0]
            if isinstance(last, list) and len(last) >= 2:
                end = last[1]
        start_ms = int(start or index * 1000)
        end_ms = int(end or max(start_ms + 1000, (index + 1) * 1000))
        return start_ms, end_ms

    def _extract_confidence(self, item: dict[str, Any]) -> float | None:
        confidence = item.get("confidence") or item.get("score")
        return float(confidence) if confidence is not None else None

    def _normalize_speaker_label(self, speaker_index: Any) -> str:
        value = str(speaker_index).replace("speaker_", "").replace("Speaker ", "")
        return f"Speaker {value}"
