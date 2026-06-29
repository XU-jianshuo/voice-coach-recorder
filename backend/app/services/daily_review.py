from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date as DateType
from datetime import datetime, time, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.adapters.base import DailyReviewAdapter
from app.adapters.deepseek import build_daily_review_adapter
from app.config import Settings
from app.models import AudioSession, CommunicationAnalysis, SessionStatus
from app.schemas import DailyReviewResponse, DailySessionSummary


@dataclass(frozen=True)
class DailyReviewAggregate:
    date: str
    valid_session_count: int
    total_duration_minutes: float
    session_summaries: list[dict[str, Any]]
    todo_count: int
    unresolved_item_count: int
    frequent_objections: list[str]
    score_averages: dict[str, float]
    todos: list[dict[str, Any]]


def build_daily_review(
    db: Session,
    review_date: str,
    settings: Settings,
    adapter: DailyReviewAdapter | None = None,
) -> DailyReviewResponse:
    aggregate = aggregate_daily_review(db, review_date)
    review_adapter = adapter or build_daily_review_adapter(settings)
    coaching = review_adapter.summarize_daily_review(
        {
            "date": aggregate.date,
            "valid_session_count": aggregate.valid_session_count,
            "total_duration_minutes": aggregate.total_duration_minutes,
            "session_summaries": aggregate.session_summaries,
            "todo_count": aggregate.todo_count,
            "unresolved_item_count": aggregate.unresolved_item_count,
            "frequent_objections": aggregate.frequent_objections,
            "score_averages": aggregate.score_averages,
            "todos": aggregate.todos,
        }
    )
    return DailyReviewResponse(
        date=aggregate.date,
        valid_session_count=aggregate.valid_session_count,
        total_duration_minutes=aggregate.total_duration_minutes,
        session_summaries=[
            DailySessionSummary(**summary) for summary in aggregate.session_summaries
        ],
        todo_count=aggregate.todo_count,
        unresolved_item_count=aggregate.unresolved_item_count,
        frequent_objections=aggregate.frequent_objections,
        score_averages=aggregate.score_averages,
        coaching_summary=coaching.raw_payload or {
            "date": coaching.date,
            "daily_summary": coaching.daily_summary,
            "valid_session_count": coaching.valid_session_count,
            "main_topics": coaching.main_topics,
            "frequent_objections": coaching.frequent_objections,
            "overall_strengths": coaching.overall_strengths,
            "overall_weaknesses": coaching.overall_weaknesses,
            "top_improvement": coaching.top_improvement,
            "best_phrase_today": coaching.best_phrase_today,
            "phrase_to_replace": coaching.phrase_to_replace,
            "priority_follow_ups": coaching.priority_follow_ups,
            "tomorrow_focus": coaching.tomorrow_focus,
        },
    )


def aggregate_daily_review(db: Session, review_date: str) -> DailyReviewAggregate:
    day = DateType.fromisoformat(review_date)
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = datetime.combine(day, time.max, tzinfo=timezone.utc)
    sessions = (
        db.scalars(
            select(AudioSession)
            .options(selectinload(AudioSession.analysis))
            .where(AudioSession.started_at >= start)
            .where(AudioSession.started_at <= end)
            .where(AudioSession.status == SessionStatus.analyzed.value)
            .order_by(AudioSession.started_at)
        )
        .unique()
        .all()
    )
    analyses = {session.id: session.analysis for session in sessions}
    session_summaries = [
        _session_summary(session, analyses.get(session.id)) for session in sessions
    ]
    todos = _collect_todos(analyses.values())
    score_averages = _average_scores(analyses.values())
    objections = _frequent_values(analyses.values(), "counterparty_objections")
    unresolved_item_count = sum(
        len(_as_list((analysis.raw_payload or {}).get("risk_flags")))
        for analysis in analyses.values()
        if analysis is not None
    )
    total_duration = round(
        sum(summary["duration_minutes"] for summary in session_summaries), 2
    )
    return DailyReviewAggregate(
        date=review_date,
        valid_session_count=len(session_summaries),
        total_duration_minutes=total_duration,
        session_summaries=session_summaries,
        todo_count=len(todos),
        unresolved_item_count=unresolved_item_count,
        frequent_objections=objections,
        score_averages=score_averages,
        todos=todos,
    )


def _session_summary(
    session: AudioSession, analysis: CommunicationAnalysis | None
) -> dict[str, Any]:
    duration = max((session.ended_at - session.started_at).total_seconds() / 60, 0)
    return {
        "session_id": session.id,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "duration_minutes": round(duration, 2),
        "scene": session.scene,
        "summary": analysis.summary if analysis else None,
    }


def _collect_todos(analyses) -> list[dict[str, Any]]:
    todos: list[dict[str, Any]] = []
    for analysis in analyses:
        if analysis is None:
            continue
        for todo in analysis.todos or []:
            if isinstance(todo, dict):
                todos.append(todo)
    return todos


def _average_scores(analyses) -> dict[str, float]:
    totals: dict[str, list[float]] = defaultdict(list)
    for analysis in analyses:
        if analysis is None:
            continue
        for key, value in (analysis.scores or {}).items():
            if isinstance(value, int | float):
                totals[key].append(float(value))
    return {
        key: round(sum(values) / len(values), 2)
        for key, values in sorted(totals.items())
        if values
    }


def _frequent_values(analyses, key: str) -> list[str]:
    counter: Counter[str] = Counter()
    for analysis in analyses:
        if analysis is None:
            continue
        for value in _as_list((analysis.raw_payload or {}).get(key)):
            counter[str(value)] += 1
    return [value for value, _count in counter.most_common(5)]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
