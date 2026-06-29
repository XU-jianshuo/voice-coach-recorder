# CODEX_TASKS.md

This file is the execution plan for Codex. Follow milestones in order. Do not implement everything at once.

## Global Rules for Codex

1. Read `PROJECT_SPEC.md` before coding.
2. Implement only the requested milestone.
3. Keep commits small and reviewable.
4. Do not hard-code API keys, tokens, server URLs or model names.
5. Use environment variables and `.env.example`.
6. Do not implement hidden recording or stealth behavior.
7. Prefer clean architecture and testable modules.
8. Add basic tests for backend logic.
9. Keep Android and backend separate.
10. Use mock adapters before integrating heavy models.

## Milestone 1: Backend Skeleton

Goal: create a working FastAPI backend that can receive audio uploads and store session records.

Tasks:

- Create `backend/` Python project.
- Use Python 3.11+.
- Add FastAPI app.
- Add config module reading environment variables.
- Add SQLAlchemy models:
  - AudioSession
  - TranscriptSegment
  - SpeakerProfile
  - CommunicationAnalysis
  - Hotword
- Use SQLite by default for local development.
- Add optional PostgreSQL connection string through environment variable.
- Add `/health` endpoint.
- Add `POST /api/v1/audio-sessions` endpoint for multipart upload.
- Save uploaded audio under configurable storage directory.
- Create DB row with status `queued`.
- Add `GET /api/v1/audio-sessions/{session_id}` endpoint.
- Add `GET /api/v1/audio-sessions/{session_id}/transcript` endpoint.
- Add `GET /api/v1/audio-sessions/{session_id}/analysis` endpoint.
- Add basic pytest tests.
- Add Dockerfile.
- Add docker-compose.yml with backend and optional redis/postgres placeholders.

Acceptance criteria:

- `docker compose up` starts the backend.
- `GET /health` returns 200.
- Upload endpoint accepts a small audio file.
- Uploaded file is saved.
- Session record is created.
- Tests pass.

Do not implement FunASR, DeepSeek or Android in this milestone.

## Milestone 2: Background Job Abstraction

Goal: create processing pipeline interfaces without heavy dependencies.

Tasks:

- Add job status lifecycle:
  - queued
  - transcribing
  - transcribed
  - analyzing
  - analyzed
  - failed
- Add simple in-process background task for development.
- Add adapter interfaces:
  - `ASRAdapter`
  - `DiarizationAdapter`
  - `AnalysisAdapter`
- Add mock ASR adapter that returns Chinese sample transcript segments.
- Add mock analysis adapter that returns deterministic JSON analysis.
- Trigger mock processing after upload.
- Store transcript segments and analysis in DB.

Acceptance criteria:

- Uploading an audio file eventually creates transcript and analysis.
- Status changes are visible through API.
- No real model dependency is required.

## Milestone 3: DeepSeek Adapter

Goal: integrate DeepSeek for structured communication analysis.

Tasks:

- Add DeepSeek client using OpenAI-compatible API style.
- Read from environment:
  - DEEPSEEK_API_KEY
  - DEEPSEEK_BASE_URL
  - DEEPSEEK_MODEL
  - DEEPSEEK_REASONING_MODEL
- Implement JSON-only response mode when available.
- Add robust JSON parsing and validation.
- Add prompt templates from `docs/deepseek-prompts.md`.
- Add fallback behavior when model output is invalid.
- Add unit tests with mocked HTTP responses.

Acceptance criteria:

- Given transcript segments, DeepSeek adapter returns valid analysis JSON.
- Secrets are never logged.
- App works without DeepSeek key by using mock adapter.

## Milestone 4: FunASR / SenseVoice Integration

Goal: integrate real Chinese speech transcription on Tencent Cloud.

Tasks:

- Add FunASR service wrapper.
- Support local model path configuration.
- Implement ASR with:
  - VAD
  - punctuation
  - hotwords
  - timestamps if available
- Implement speaker diarization with CAM++ or available FunASR pipeline.
- Normalize model output into TranscriptSegment rows.
- Keep ASR adapter swappable.
- Add clear install/deploy documentation.

Acceptance criteria:

- A Chinese audio file can be transcribed.
- Output includes timestamped text.
- Speaker labels are normalized as `Speaker 0`, `Speaker 1`, etc.
- Hotwords can improve insurance/business terms.

## Milestone 5: Speaker Profiles and Manual Correction

Goal: make speaker identity useful for coaching.

Tasks:

- Add speaker profile API.
- Support `self` speaker profile for the user.
- Add endpoint to update speaker label for transcript segment.
- Store corrections and apply consistent labels within same session.
- Add optional fields for voiceprint metadata.
- Do not overclaim speaker identity; use `疑似` for inferred known speakers.

Acceptance criteria:

- User can label Speaker 0 as `我`.
- All relevant segments can display corrected label.
- Transcript API returns corrected speaker labels.

## Milestone 6: Hotword Management

Goal: support insurance and business vocabulary.

Tasks:

- Add Hotword model and API.
- Provide default hotword seed list:
  - 车险
  - 驾意险
  - 承运人
  - 续保率
  - 赔付率
  - 费用率
  - 联动率
  - 件均
  - 分公司
  - 中支
  - 专代
  - 司控
  - 统扩
  - 清单
  - 核保
  - 报价
  - 录单
  - 通报
- Pass hotwords to ASR adapter when supported.

Acceptance criteria:

- User can list/create/delete hotwords.
- ASR adapter receives configured hotwords.

## Milestone 7: Android MVP

Goal: create Android client for public recording and upload.

Tasks:

- Create Android Kotlin project under `android/VoiceCoachRecorder`.
- Use Jetpack Compose.
- Implement foreground recording service.
- Use AudioRecord or MediaRecorder depending on final design.
- Show persistent notification while recording.
- Implement start/stop/pause controls.
- Save audio to app-private storage.
- Upload audio to backend.
- Show session list, transcript and analysis.
- Store server URL and device token securely.

Acceptance criteria:

- App can record visibly.
- Recording notification is always shown.
- App can upload a file to backend.
- App can display transcript and analysis from backend.

## Milestone 8: Daily Review

Goal: create daily communication dashboard.

Tasks:

- Add daily review API.
- Aggregate sessions by date.
- Calculate:
  - number of valid sessions
  - total duration
  - user speaking ratio if speaker is known
  - action item count
  - unresolved items
  - frequent objections
- Use DeepSeek to produce daily coaching summary.
- Display daily review in Android app.

Acceptance criteria:

- `GET /api/v1/daily-review?date=YYYY-MM-DD` returns structured review.
- Android app can display daily review.

## Milestone 9: Deployment Hardening

Goal: make the system stable on Tencent Cloud.

Tasks:

- Add production docker compose template.
- Add nginx reverse proxy example.
- Add HTTPS notes.
- Add systemd service example.
- Add log rotation guidance.
- Add backup strategy.
- Add storage retention settings.
- Add security checklist.

Acceptance criteria:

- Deployment docs can be followed on a clean Tencent Cloud Ubuntu server.
- No secrets are committed.
- Storage and database paths are configurable.

## Suggested First Codex Prompt

Use this exact prompt in Codex:

```text
Read PROJECT_SPEC.md and CODEX_TASKS.md. Start with Milestone 1 only. Implement the backend skeleton with FastAPI, SQLAlchemy models, upload endpoint, health check, environment config, SQLite default database, and Docker Compose. Add basic pytest tests. Do not implement Android, FunASR, DeepSeek, or real background workers yet.
```
