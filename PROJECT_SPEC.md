# PROJECT_SPEC.md

## 1. Project Vision

Voice Coach Recorder is a personal communication coaching system for Chinese business conversations.

It records conversations openly on Android, uploads valid sessions to a Tencent Cloud server, uses local/self-hosted speech models to transcribe and separate speakers, then uses DeepSeek to analyze the user's communication performance.

The system is not designed for hidden recording. It must always make recording visible and controllable.

## 2. Target User

Primary user: a Chinese insurance product/channel/business manager who frequently talks with clients, channels, branches and team members.

Main value:

- Preserve key external conversations.
- Turn spoken conversations into searchable structured text.
- Identify what the user said versus what other people said.
- Extract action items, objections, commitments and follow-up deadlines.
- Analyze whether the user communicated clearly, handled objections, controlled rhythm and closed responsibilities.

## 3. Product Scope

### 3.1 Android App

The Android app is a stable public recorder and review client.

Responsibilities:

- Foreground service recording with persistent notification.
- Clear recording status shown to the user and Android system.
- Audio capture using AudioRecord.
- Lightweight local voice activity detection if feasible.
- Session-level segmentation rather than naive fixed 10-minute files.
- Encrypted local cache.
- Upload audio only under configured conditions, such as Wi-Fi and charging.
- Display transcripts, speakers, analysis and daily reviews.
- Allow manual correction of speaker labels.
- Manage hotwords and user voice profile metadata.

Non-goals for first version:

- No hidden background recording.
- No stealth mode.
- No heavy ASR model inference on phone.
- No automatic recording of phone calls unless explicitly implemented later with platform-compliant APIs.

### 3.2 Backend

The backend is the private processing center on Tencent Cloud.

Responsibilities:

- Receive audio uploads from Android.
- Store raw audio files and processing status.
- Queue ASR and analysis jobs.
- Run FunASR / SenseVoice for ASR, VAD, punctuation and diarization.
- Save transcript segments with timestamps and speaker labels.
- Manage speaker profiles and manual label corrections.
- Call DeepSeek to generate conversation analysis and daily reviews.
- Provide API endpoints for the Android app.

### 3.3 Model Layer

Preferred speech model stack:

1. FunASR / Paraformer / SenseVoice for Chinese ASR, VAD, punctuation, hotwords and diarization.
2. CAM++ or compatible speaker embedding / diarization component.
3. sherpa-onnx as optional edge/offline fallback.
4. WhisperX / faster-whisper only as baseline or fallback.

### 3.4 Analysis Layer

DeepSeek is used only for text analysis, not speech transcription.

DeepSeek must receive structured transcript data, including speaker labels and timestamps.

Analysis output must be structured JSON, not free-form only.

## 4. Core Data Model

### 4.1 AudioSession

```json
{
  "id": "session_20260625_093012",
  "device_id": "android_xxx",
  "started_at": "2026-06-25T09:30:12+08:00",
  "ended_at": "2026-06-25T09:52:40+08:00",
  "status": "analyzed",
  "audio_path": "audio/2026/06/25/session_093012.m4a",
  "scene": "渠道沟通",
  "privacy_level": "work"
}
```

### 4.2 TranscriptSegment

```json
{
  "session_id": "session_20260625_093012",
  "start_ms": 1200,
  "end_ms": 8500,
  "speaker_id": "speaker_me",
  "speaker_label": "我",
  "text": "今天主要跟你确认一下车险续保和驾意险联动的推进节奏。",
  "confidence": 0.91
}
```

### 4.3 SpeakerProfile

```json
{
  "id": "speaker_me",
  "display_name": "我",
  "type": "self",
  "voiceprint_path": "speaker_profiles/me.embedding",
  "created_at": "2026-06-25T09:00:00+08:00"
}
```

### 4.4 CommunicationAnalysis

```json
{
  "session_id": "session_20260625_093012",
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
  "strengths": ["开场目标较清楚", "能回应对方费用政策顾虑"],
  "weaknesses": ["没有明确责任人", "没有要求对方给出具体完成时间"],
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
      "improved": "这件事今天先定负责人和时间点，周三前给我第一版清单，周五我们看试点转化。"
    }
  ]
}
```

## 5. Communication Analysis Dimensions

DeepSeek analysis must evaluate these dimensions:

1. Goal clarity: Did the user make the purpose clear?
2. Question quality: Did the user identify real constraints and objections?
3. Business actionability: Were instructions concrete and executable?
4. Responsibility closure: Were owner, deadline and deliverable defined?
5. Objection handling: Did the user address concerns such as cost, policy, resources and workflow?
6. Rhythm control: Did the user control the conversation or get led away?
7. Expression efficiency: Was the user concise or repetitive?
8. Follow-up closure: Were next steps and reminders created?

## 6. API Overview

### Health Check

`GET /health`

### Create Audio Session

`POST /api/v1/audio-sessions`

Multipart form:

- audio: file
- device_id: string
- started_at: datetime
- ended_at: datetime
- metadata: optional JSON string

Response:

```json
{
  "session_id": "session_xxx",
  "status": "queued"
}
```

### Get Session

`GET /api/v1/audio-sessions/{session_id}`

### Get Transcript

`GET /api/v1/audio-sessions/{session_id}/transcript`

### Get Analysis

`GET /api/v1/audio-sessions/{session_id}/analysis`

### Update Speaker Label

`PATCH /api/v1/transcript-segments/{segment_id}/speaker`

### Hotwords

- `GET /api/v1/hotwords`
- `POST /api/v1/hotwords`
- `DELETE /api/v1/hotwords/{id}`

### Daily Review

`GET /api/v1/daily-review?date=YYYY-MM-DD`

## 7. Security and Compliance

- Recording must be explicit and visible.
- Android notification must stay visible while recording.
- Audio files must be stored in app-private storage.
- Upload must use HTTPS.
- Server must require device token authentication.
- DeepSeek must receive only transcript text, not raw audio.
- Secrets must be stored in environment variables, never committed.
- The app must provide one-tap pause/stop.
- The system must allow deletion of sessions and audio files.

## 8. First Version Definition of Done

A first usable MVP is complete when:

- Backend starts with Docker Compose.
- `/health` works.
- Android or curl can upload an audio file.
- Uploaded session is saved to local storage.
- A transcript job is queued.
- A placeholder ASR adapter can create mock transcript segments.
- DeepSeek adapter can analyze a provided transcript into JSON.
- Session transcript and analysis can be retrieved through API.

Real FunASR and Android recording can be implemented after backend skeleton is stable.
