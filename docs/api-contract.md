# API Contract

Base prefix: `/api/v1`

Authentication: device token in header.

```http
Authorization: Bearer <DEVICE_TOKEN>
```

## Health

### GET /health

Response:

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

Fields:

- `audio`: file, required.
- `device_id`: string, required.
- `started_at`: ISO datetime string, required.
- `ended_at`: ISO datetime string, required.
- `metadata`: JSON string, optional.

Example response:

```json
{
  "session_id": "session_20260625_093012_abcd",
  "status": "queued"
}
```

### GET /api/v1/audio-sessions/{session_id}

Response:

```json
{
  "id": "session_20260625_093012_abcd",
  "device_id": "android_xxx",
  "started_at": "2026-06-25T09:30:12+08:00",
  "ended_at": "2026-06-25T09:52:40+08:00",
  "status": "analyzed",
  "scene": "渠道沟通",
  "privacy_level": "work",
  "created_at": "2026-06-25T09:53:00+08:00"
}
```

### GET /api/v1/audio-sessions

Query parameters:

- `date`: optional, YYYY-MM-DD.
- `status`: optional.
- `limit`: optional, default 50.
- `offset`: optional, default 0.

Response:

```json
{
  "items": [],
  "limit": 50,
  "offset": 0
}
```

## Transcript

### GET /api/v1/audio-sessions/{session_id}/transcript

Response:

```json
{
  "session_id": "session_20260625_093012_abcd",
  "segments": [
    {
      "id": "seg_001",
      "start_ms": 1200,
      "end_ms": 8500,
      "speaker_id": "speaker_me",
      "speaker_label": "我",
      "text": "今天主要跟你确认一下车险续保和驾意险联动的推进节奏。",
      "confidence": 0.91
    }
  ]
}
```

## Analysis

### GET /api/v1/audio-sessions/{session_id}/analysis

Response:

```json
{
  "session_id": "session_20260625_093012_abcd",
  "summary": "本次沟通围绕渠道推动节奏、费用政策和客户清单展开。",
  "scores": {
    "goal_clarity": 8,
    "question_quality": 7,
    "business_actionability": 7,
    "responsibility_closure": 5,
    "objection_handling": 7,
    "rhythm_control": 6,
    "expression_efficiency": 6,
    "follow_up_closure": 6
  },
  "strengths": ["开场目标较清楚"],
  "weaknesses": ["没有明确责任人"],
  "todos": [
    {
      "owner": "我",
      "task": "确认费用政策边界",
      "due_date": "2026-06-26"
    }
  ],
  "better_phrases": [
    {
      "original": "你们先推进一下。",
      "improved": "这件事今天先定负责人和时间点，周三前给我第一版清单。"
    }
  ]
}
```

## Speaker Labels

### PATCH /api/v1/transcript-segments/{segment_id}/speaker

Request:

```json
{
  "speaker_label": "我",
  "speaker_profile_id": "speaker_me",
  "apply_to_session": true
}
```

Response:

```json
{
  "segment_id": "seg_001",
  "speaker_label": "我",
  "updated": true
}
```

## Speaker Profiles

### GET /api/v1/speaker-profiles

### POST /api/v1/speaker-profiles

Request:

```json
{
  "display_name": "我",
  "type": "self"
}
```

## Hotwords

### GET /api/v1/hotwords

Response:

```json
{
  "items": [
    {
      "id": "hotword_001",
      "text": "驾意险",
      "category": "insurance_product",
      "weight": 10
    }
  ]
}
```

### POST /api/v1/hotwords

Request:

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

Response:

```json
{
  "date": "2026-06-25",
  "valid_session_count": 6,
  "total_duration_minutes": 135,
  "user_speaking_ratio": 0.42,
  "action_item_count": 4,
  "unresolved_item_count": 2,
  "frequent_objections": ["费用政策", "产品支持", "系统流程"],
  "summary": "今天对外沟通主要集中在渠道推动和续保联动。",
  "top_improvement": {
    "problem": "责任压实不足",
    "suggestion": "每次沟通结束前明确责任人、时间点和交付物。"
  }
}
```

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
