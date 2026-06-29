from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.db import Base, create_engine_for
from app.models import AudioSession, CommunicationAnalysis, SessionStatus
from app.services.daily_review import build_daily_review


def add_session(
    db,
    session_id: str,
    start: datetime,
    end: datetime,
    summary: str,
    scores: dict,
    todos: list,
    raw_payload: dict | None = None,
):
    db.add(
        AudioSession(
            id=session_id,
            device_id="android_test",
            started_at=start,
            ended_at=end,
            status=SessionStatus.analyzed.value,
            audio_path=f"audio/{session_id}.m4a",
            scene="channel",
            privacy_level="work",
        )
    )
    db.add(
        CommunicationAnalysis(
            session_id=session_id,
            summary=summary,
            scores=scores,
            strengths=[],
            weaknesses=[],
            todos=todos,
            better_phrases=[],
            raw_payload=raw_payload or {},
        )
    )


def test_daily_review_aggregates_analyzed_sessions_with_mock_summary(test_settings):
    engine = create_engine_for(test_settings)
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_local()
    try:
        add_session(
            db,
            "session_one",
            datetime(2026, 6, 25, 9, 0, tzinfo=timezone.utc),
            datetime(2026, 6, 25, 9, 30, tzinfo=timezone.utc),
            "续保推进沟通",
            {"goal_clarity": 8, "question_quality": 6},
            [{"task": "确认清单", "owner": "我"}],
            {"counterparty_objections": ["费用政策不清晰"], "risk_flags": ["未明确截止时间"]},
        )
        add_session(
            db,
            "session_two",
            datetime(2026, 6, 25, 14, 0, tzinfo=timezone.utc),
            datetime(2026, 6, 25, 14, 15, tzinfo=timezone.utc),
            "分公司汇报",
            {"goal_clarity": 6, "question_quality": 8},
            [],
            {"counterparty_objections": ["费用政策不清晰"]},
        )
        add_session(
            db,
            "session_other_day",
            datetime(2026, 6, 26, 9, 0, tzinfo=timezone.utc),
            datetime(2026, 6, 26, 9, 15, tzinfo=timezone.utc),
            "其他日期",
            {"goal_clarity": 10},
            [],
        )
        db.commit()

        review = build_daily_review(db, "2026-06-25", test_settings)

        assert review.date == "2026-06-25"
        assert review.valid_session_count == 2
        assert review.total_duration_minutes == 45
        assert len(review.session_summaries) == 2
        assert review.todo_count == 1
        assert review.unresolved_item_count == 1
        assert review.frequent_objections == ["费用政策不清晰"]
        assert review.score_averages["goal_clarity"] == 7
        assert review.coaching_summary["daily_summary"].startswith("Mock daily review")
    finally:
        db.close()


def test_daily_review_api_returns_mock_aggregation(client, auth_headers):
    payload = {
        "device_id": "android_test",
        "started_at": "2026-06-25T09:00:00+00:00",
        "ended_at": "2026-06-25T09:03:00+00:00",
        "metadata": '{"scene":"channel","privacy_level":"work"}',
    }

    response = client.post(
        "/api/v1/audio-sessions",
        data=payload,
        files={"audio": ("sample.m4a", b"fake audio", "audio/mp4")},
        headers=auth_headers,
    )
    assert response.status_code == 201

    review_response = client.get(
        "/api/v1/daily-review?date=2026-06-25",
        headers=auth_headers,
    )

    assert review_response.status_code == 200
    body = review_response.json()
    assert body["date"] == "2026-06-25"
    assert body["valid_session_count"] == 1
    assert body["todo_count"] == 1
    assert body["coaching_summary"]["date"] == "2026-06-25"
