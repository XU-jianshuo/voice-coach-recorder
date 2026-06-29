# API Contract

Base prefix: `/api/v1`

Authentication: device token in header.

```http
Authorization: Bearer <DEVICE_TOKEN>
```

## Health

### GET /health

```json
{
  "status": "ok",
  "app": "Voice Coach Recorder"
}
```

## Audio Sessions

### POST /api/v1/audio-sessions

Create an audio session and upload audio.

Content type: `multipart/form-data`

- `audio`: file, required
- `device_id`: string, required
- `started_at`: ISO datetime string, required
- `ended_at`: ISO datetime string, required
- `metadata`: JSON string, optional

```json
{
  "session_id": "session_20260625_093012_abcd",
  "status": "queued"
}
```

### GET /api/v1/audio-sessions/{session_id}

```json
{
  "id": "session_20260625_093012_abcd",
  "device_id": "android_xxx",
  "started_at": "2026-06-25T09:30:12+08:00",
  "ended_at": "2026-06-25T09:52:40+08:00",
  "status": "analyzed",
  "scene": "channel",
  "privacy_level": "work",
  "created_at": "2026-06-25T09:53:00+08:00"
}
```

## Transcript

### GET /api/v1/audio-sessions/{session_id}/transcript

```json
{
  "session_id": "session_20260625_093012_abcd",
  "segments": [
    {
      "id": 1,
      "start_ms": 1200,
      "end_ms": 8500,
      "speaker_id": "speaker_0",
      "speaker_label": "Speaker 0",
      "text": "今天主要确认续保推进清单。",
      "confidence": 0.91
    }
  ]
}
```

## Analysis

### GET /api/v1/audio-sessions/{session_id}/analysis

```json
{
  "session_id": "session_20260625_093012_abcd",
  "summary": "本次沟通围绕续保推进和后续动作展开。",
  "scores": {
    "goal_clarity": 8,
    "question_quality": 7
  },
  "strengths": ["开场目标清楚"],
  "weaknesses": ["责任人还可以更明确"],
  "todos": [
    {
      "owner": "我",
      "task": "确认费用政策边界",
      "due_date": "2026-06-26"
    }
  ],
  "better_phrases": [
    {
      "original": "你们先推进一下",
      "improved": "请明天下午前给第一版清单，并标明责任人和完成时间。"
    }
  ]
}
```

## Speaker Labels

### PATCH /api/v1/transcript-segments/{segment_id}/speaker

```json
{
  "speaker_label": "疑似张三",
  "speaker_profile_id": "speaker_known",
  "apply_to_session": true
}
```

```json
{
  "segment_id": 1,
  "speaker_label": "疑似张三",
  "updated": true
}
```

## Speaker Profiles

### GET /api/v1/speaker-profiles

### POST /api/v1/speaker-profiles

```json
{
  "display_name": "我",
  "type": "self"
}
```

Supported `type` values: `self`, `known`, `unknown`.

## Hotwords

### GET /api/v1/hotwords

### POST /api/v1/hotwords

```json
{
  "text": "统扩",
  "category": "business_action",
  "weight": 10
}
```

### DELETE /api/v1/hotwords/{id}

## Daily Review

### GET /api/v1/daily-review?date=YYYY-MM-DD

```json
{
  "date": "2026-06-25",
  "valid_session_count": 2,
  "total_duration_minutes": 45,
  "session_summaries": [
    {
      "session_id": "session_20260625_090000_abcd",
      "started_at": "2026-06-25T09:00:00+00:00",
      "ended_at": "2026-06-25T09:30:00+00:00",
      "duration_minutes": 30,
      "scene": "channel",
      "summary": "续保推进沟通"
    }
  ],
  "todo_count": 4,
  "unresolved_item_count": 2,
  "frequent_objections": ["费用政策不清晰"],
  "score_averages": {
    "goal_clarity": 7,
    "question_quality": 7
  },
  "coaching_summary": {
    "date": "2026-06-25",
    "daily_summary": "Daily review summary",
    "valid_session_count": 2,
    "main_topics": ["续保推进"],
    "frequent_objections": ["费用政策不清晰"],
    "overall_strengths": ["目标清楚"],
    "overall_weaknesses": ["闭环不足"],
    "top_improvement": {
      "problem": "责任人不明确",
      "why_it_matters": "影响执行",
      "suggestion": "结束前确认责任人"
    },
    "best_phrase_today": "请明天下午给第一版清单。",
    "phrase_to_replace": {
      "original": "推进一下",
      "improved": "请明天下午前给第一版清单。"
    },
    "priority_follow_ups": [],
    "tomorrow_focus": ["确认闭环"]
  }
}
```

## ASR Provider Configuration

- `ASR_PROVIDER=mock`: default local development path.
- `ASR_PROVIDER=funasr`: optional FunASR/SenseVoice path.

When `funasr` is selected, `FUNASR_MODEL_DIR` must point at installed model files and
the runtime must include optional FunASR dependencies. Missing dependencies or model files
fail the processing session clearly without preventing the API server from starting.

## Status Lifecycle

AudioSession status values:

- `queued`
- `transcribing`
- `transcribed`
- `analyzing`
- `analyzed`
- `failed`

## Error Format

```json
{
  "error": {
    "code": "invalid_request",
    "message": "started_at is required"
  }
}
```
