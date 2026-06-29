# Voice Coach Recorder Android MVP

This is the Milestone 7 Android MVP for the Voice Coach Recorder project.

## Scope

Implemented:

- Kotlin Android app under `android/VoiceCoachRecorder`.
- Jetpack Compose UI.
- Visible foreground microphone recording service.
- Persistent recording notification while recording or paused.
- Start, pause/resume and stop controls.
- App-private recording storage under the app external files directory.
- Local session list.
- Backend settings for server URL and device token.
- Upload to `POST /api/v1/audio-sessions`.
- Transcript display from `GET /api/v1/audio-sessions/{session_id}/transcript`.
- Analysis display from `GET /api/v1/audio-sessions/{session_id}/analysis`.
- Daily review display from `GET /api/v1/daily-review?date=YYYY-MM-DD`.

Not implemented:

- Hidden recording.
- Stealth recording.
- Phone-call recording.
- On-device ASR.
- Android-side FunASR/SenseVoice.

## Open In Android Studio

1. Install Android Studio with Android SDK 35.
2. Open the folder:

   ```text
   android/VoiceCoachRecorder
   ```

3. Let Android Studio sync Gradle.
4. Create a debug run configuration for the `app` module.
5. Run on a physical Android device for microphone and foreground service testing.

## Backend Settings

In the app, set:

- Server URL: for Android emulator, usually `http://10.0.2.2:8000`; for a real device, use the LAN or HTTPS server URL.
- Device token: must match backend `DEVICE_TOKEN`.

The app sends:

```http
Authorization: Bearer <device token>
```

## Permissions

Declared in `AndroidManifest.xml`:

- `INTERNET`
- `RECORD_AUDIO`
- `FOREGROUND_SERVICE`
- `FOREGROUND_SERVICE_MICROPHONE`
- `POST_NOTIFICATIONS`

The app requests microphone permission at runtime. On Android 13+, notification permission is also requested at runtime. Recording is started only after required permissions are granted.

## Recording Behavior

Recording uses `MediaRecorder` with:

- microphone audio source;
- MPEG-4 container;
- AAC audio encoder;
- `.m4a` files in app-private storage.

The foreground service starts immediately when recording starts and shows an ongoing notification with pause/resume and stop actions.

## Build And Test

From Android Studio:

- Sync Gradle.
- Run `app`.
- Run unit tests from the test panel.

From command line, if Java, Android SDK and Gradle are installed:

```powershell
cd android/VoiceCoachRecorder
gradle testDebugUnitTest
gradle assembleDebug
```

This repository does not commit secrets or `local.properties`.

## Manual Device Testing Checklist

- Grant microphone and notification permissions.
- Start recording and confirm the persistent notification is visible.
- Pause and resume from both the app and notification.
- Stop recording and confirm a local session appears.
- Upload to the backend and confirm a backend session ID appears.
- Fetch transcript and analysis after backend processing finishes.
- Fetch daily review after at least one analyzed session exists for today.
