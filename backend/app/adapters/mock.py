from app.adapters.base import AnalysisData, DailyReviewData, TranscriptSegmentData
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


class MockDailyReviewAdapter:
    def summarize_daily_review(self, payload: dict) -> DailyReviewData:
        date = payload["date"]
        valid_session_count = payload["valid_session_count"]
        todo_count = payload["todo_count"]
        frequent_objections = payload["frequent_objections"]
        review = {
            "date": date,
            "daily_summary": (
                f"Mock daily review for {date}: {valid_session_count} valid sessions, "
                f"{todo_count} follow-up items."
            ),
            "valid_session_count": valid_session_count,
            "main_topics": [
                item["summary"] for item in payload["session_summaries"][:3]
            ],
            "frequent_objections": frequent_objections,
            "overall_strengths": ["沟通目标和推进事项有基础记录"],
            "overall_weaknesses": ["后续仍需压实责任人、截止时间和交付物"],
            "top_improvement": {
                "problem": "跟进闭环不够稳定",
                "why_it_matters": "没有明确闭环会降低沟通后的执行质量",
                "suggestion": "每次沟通结束前确认责任人、时间点和下一次检查节点",
            },
            "best_phrase_today": "请给出责任人、截止时间和第一版清单。",
            "phrase_to_replace": {
                "original": "你们先推进一下",
                "improved": "请明天下午前给第一版清单，并标明责任人和完成时间。",
            },
            "priority_follow_ups": payload["todos"][:5],
            "tomorrow_focus": ["优先确认未闭环事项", "继续追问高频异议"],
        }
        return DailyReviewData(raw_payload=review, **review)
