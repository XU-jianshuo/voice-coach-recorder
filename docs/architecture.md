# Architecture

## High-Level Architecture

```text
Android App
  ├─ public foreground recording
  ├─ local session segmentation
  ├─ encrypted cache
  └─ upload client
        ↓ HTTPS
Tencent Cloud Backend
  ├─ FastAPI API server
  ├─ database
  ├─ audio storage
  ├─ ASR worker
  ├─ diarization worker
  └─ analysis worker
        ↓ text only
DeepSeek API
  └─ communication analysis / daily review
```

## Component Responsibilities

### Android App

Android is the acquisition and review layer. It must not run heavy speech models in the first version.

Key modules:

- `RecordingService`: foreground service for visible recording.
- `SessionManager`: creates and finalizes local recording sessions.
- `UploadWorker`: uploads cached sessions under configured network conditions.
- `ApiClient`: talks to backend.
- `TranscriptScreen`: displays transcript and speaker labels.
- `AnalysisScreen`: displays coaching output.
- `SettingsScreen`: server URL, token, upload policy and hotwords.

### Backend API Server

FastAPI provides app-facing APIs.

Key modules:

- `config`: environment variables.
- `db`: SQLAlchemy engine/session.
- `models`: database tables.
- `schemas`: Pydantic request/response models.
- `routers`: API endpoints.
- `services/storage`: audio file storage.
- `services/pipeline`: orchestration of ASR and analysis jobs.
- `adapters/asr`: mock, FunASR, SenseVoice adapters.
- `adapters/analysis`: mock and DeepSeek adapters.

### Speech Model Layer

First production target:

- FunASR / Paraformer for Chinese ASR.
- FSMN-VAD for voice activity detection.
- CT-Punc for punctuation.
- CAM++ / compatible speaker pipeline for diarization.
- SenseVoice for future emotion/audio-event understanding.

ASR output must be normalized into internal `TranscriptSegment` format:

```json
{
  "start_ms": 0,
  "end_ms": 1200,
  "speaker_label": "Speaker 0",
  "text": "这里是转写文本。",
  "confidence": 0.9
}
```

### Analysis Layer

DeepSeek receives transcript JSON, not audio.

Input includes:

- session metadata
- transcript segments
- speaker labels
- hotwords if relevant
- optional user role prompt

Output must be JSON with:

- summary
- scores
- strengths
- weaknesses
- todos
- better_phrases
- risks
- follow_up_questions

## Processing Flow

1. Android records a visible session.
2. Android uploads audio with metadata.
3. Backend creates `AudioSession(status='queued')`.
4. Background job starts ASR.
5. ASR creates transcript segments.
6. Backend updates status to `transcribed`.
7. Analysis job calls DeepSeek.
8. Backend stores `CommunicationAnalysis`.
9. Android fetches transcript and analysis.
10. User may correct speaker labels.

## Session Segmentation Strategy

The product should not blindly transcribe 24 hours of audio.

Preferred logic:

```text
continuous microphone capture
→ local VAD / energy threshold
→ start session if speech continues long enough
→ end session after silence threshold
→ discard too-short/noisy sessions
→ upload valid sessions
```

Suggested defaults:

- minimum speech duration to start session: 20 seconds
- silence threshold to end session: 90 seconds
- maximum session length before forced split: 30 minutes
- minimum valid session length: 30 seconds

## Speaker Strategy

Speaker identification has four levels:

1. Diarization: `Speaker 0`, `Speaker 1`, etc.
2. Self identification: map one speaker to `我` via user voice profile or manual correction.
3. Known speaker hints: `疑似张总`, not absolute identification.
4. Role inference: `分公司负责人`, `渠道经理`, etc. inferred by DeepSeek from text.

The app must not overclaim exact identity without user confirmation.

## Hotword Strategy

Hotwords are important for insurance/business vocabulary.

Default categories:

- Insurance products: 车险、驾意险、承运人责任险、旅游意外险、景区意外险、家财险、百万医疗。
- Metrics: 续保率、赔付率、费用率、联动率、件均、满期赔付率、企划保费。
- Organization: 总公司、分公司、中支、渠道、专代、司控、个客、个非车。
- Actions: 摸排、清单、转化、二次加购、统扩、批复、核保、报价、录单、通报。

## Security

- Device token required for app APIs.
- HTTPS required in production.
- Secrets must only be in environment variables.
- Audio stored under configurable private server directory.
- Add delete endpoints before real daily use.
- Avoid logging raw transcripts unless debug mode is explicitly enabled.

## Deployment Phases

### Phase 1: Development

- FastAPI + SQLite + mock ASR + mock analysis.

### Phase 2: Private Server MVP

- FastAPI + SQLite/PostgreSQL + local audio storage + DeepSeek.

### Phase 3: Real ASR

- Add FunASR / SenseVoice.
- Add diarization.
- Add hotwords.

### Phase 4: Android MVP

- Public recording app.
- Upload and review.

### Phase 5: Production Hardening

- Nginx + HTTPS.
- Postgres.
- Redis queue.
- Backups.
- Retention rules.
