from app.adapters.base import AnalysisData, TranscriptSegmentData
from app.models import AudioSession


class MockASRAdapter:
    def transcribe(
        self, session: AudioSession, hotwords: list[str] | None = None
    ) -> list[TranscriptSegmentData]:
        return [
            TranscriptSegmentData(
                start_ms=0,
                end_ms=4200,
                speaker_id="speaker_me",
                speaker_label="我",
                text="今天我们先确认续保推进清单和各分公司的责任人。",
                confidence=0.96,
            ),
            TranscriptSegmentData(
                start_ms=4300,
                end_ms=8300,
                speaker_id="speaker_counterparty",
                speaker_label="对方",
                text="费用政策还需要再明确一下，清单我们明天下午给第一版。",
                confidence=0.93,
            ),
        ]


class NoOpDiarizationAdapter:
    def assign_speakers(
        self, segments: list[TranscriptSegmentData]
    ) -> list[TranscriptSegmentData]:
        return segments


class MockAnalysisAdapter:
    def analyze(
        self, session: AudioSession, segments: list[TranscriptSegmentData]
    ) -> AnalysisData:
        payload = {
            "summary": "模拟分析：本次沟通围绕续保推进和后续动作展开。",
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
            "strengths": ["开场目标清楚", "能围绕清单和责任人推进"],
            "weaknesses": ["费用政策边界还需要进一步压实"],
            "todos": [
                {
                    "owner": "我",
                    "task": "确认续保推进清单",
                    "due_date": "2026-06-26",
                }
            ],
            "better_phrases": [
                {
                    "original": "你们先推进一下。",
                    "improved": "请明天下午给第一版清单，并标明责任人和完成时间。",
                }
            ],
        }
        return AnalysisData(raw_payload=payload, **payload)
