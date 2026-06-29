# Android Real-Device Manual Test Checklist

Use this checklist after the Android MVP is built and the backend is running locally or on a reachable test server. This is a manual verification guide only; it does not add new app behavior.

## 1. Start Backend With Mock Processing

- [ ] Create or update backend environment settings from `.env.example`.
- [ ] Confirm mock ASR is enabled:
  - `ASR_PROVIDER=mock`
- [ ] Confirm DeepSeek is disabled or not configured for mock analysis fallback:
  - `USE_DEEPSEEK=false`
- [ ] Start the backend:
  - `uvicorn app.main:app --reload`
  - or `docker compose up --build`
- [ ] Open the health endpoint and confirm it responds:
  - `GET http://localhost:8000/health`
- [ ] Confirm the API base URL to use on the phone:
  - Android emulator: `http://10.0.2.2:8000`
  - Real device on the same Wi-Fi: `http://<computer-lan-ip>:8000`
  - Remote server: `https://<server-domain>`

## 2. Import And Build Android App

- [ ] Open Android Studio.
- [ ] Choose **Open** and select `android/VoiceCoachRecorder`.
- [ ] Wait for Gradle sync to finish.
- [ ] Confirm the `app` run configuration exists.
- [ ] Build the project.
- [ ] Run unit tests if available from Android Studio or command line:
  - `gradle testDebugUnitTest`

## 3. Install On Real Android Device

- [ ] Enable Developer Options on the device.
- [ ] Enable USB debugging.
- [ ] Connect the device by USB.
- [ ] Accept the debugging prompt on the phone.
- [ ] Select the physical device in Android Studio.
- [ ] Run the `app` configuration.
- [ ] Confirm the app opens on the phone.

## 4. Permission Flows

### Microphone Permission

- [ ] Tap the recording start control.
- [ ] Confirm Android shows the microphone permission prompt.
- [ ] Allow microphone access.
- [ ] Confirm recording can start after permission is granted.
- [ ] Repeat once with permission denied if practical, then confirm the app does not record without permission.

### Notification Permission

- [ ] On Android 13 or later, confirm Android shows the notification permission prompt.
- [ ] Allow notifications.
- [ ] Confirm a persistent recording notification appears while recording or paused.
- [ ] If notification permission is denied, confirm recording behavior is blocked or clearly not usable until notification permission is allowed.

## 5. Recording Controls

### Start Recording

- [ ] Tap start in the app.
- [ ] Confirm the UI shows an active recording state.
- [ ] Confirm the persistent foreground service notification is visible.
- [ ] Speak for at least 10 seconds.

### Pause And Resume From App

- [ ] Tap pause in the app.
- [ ] Confirm the UI shows paused state.
- [ ] Confirm the notification remains visible.
- [ ] Tap resume in the app.
- [ ] Confirm recording resumes.
- [ ] Speak for another 5 seconds.

### Pause And Resume From Notification

- [ ] Pull down the notification shade.
- [ ] Tap pause from the recording notification.
- [ ] Confirm the app UI updates to paused state.
- [ ] Tap resume from the notification.
- [ ] Confirm the app UI updates to recording state.

### Stop Recording

- [ ] Tap stop in the app or notification.
- [ ] Confirm recording stops.
- [ ] Confirm the foreground notification is dismissed.
- [ ] Confirm a new session appears in the session list.

## 6. Verify Local Recording File

- [ ] In the app, note the new session timestamp or file name.
- [ ] Use Android Studio Device Explorer.
- [ ] Browse the app-private external files area for the app package.
- [ ] Confirm a `.m4a` recording file exists.
- [ ] Confirm the file size is greater than zero.
- [ ] Pull the file locally if needed and play it to confirm audio was captured.

## 7. Backend Settings

- [ ] Open backend settings in the app.
- [ ] Set server URL:
  - For a real device on local Wi-Fi, use `http://<computer-lan-ip>:8000`.
  - Do not use `localhost` on a real phone unless the backend runs on the phone.
- [ ] Set the device token expected by the backend test configuration.
- [ ] Save settings.

## 8. Upload And Review Results

### Upload Recording

- [ ] Select the recorded session.
- [ ] Tap upload.
- [ ] Confirm upload completes successfully.
- [ ] Confirm the session has a backend session ID.
- [ ] Confirm backend logs show the upload request.

### Fetch Transcript

- [ ] Tap fetch transcript.
- [ ] Confirm Chinese mock transcript segments are displayed.
- [ ] Confirm speaker labels are generic, such as `Speaker 0` or `Speaker 1`, unless manually corrected in backend tests.

### Fetch Analysis

- [ ] Tap fetch analysis.
- [ ] Confirm deterministic mock analysis JSON or formatted analysis is displayed.
- [ ] Confirm no DeepSeek API key is required when `USE_DEEPSEEK=false`.

### Fetch Daily Review

- [ ] Tap daily review for today's date if the app exposes it.
- [ ] Confirm the response includes the uploaded session in daily totals.
- [ ] Confirm mock daily coaching output is displayed when DeepSeek is disabled.

## 9. Common Troubleshooting

### Phone Cannot Reach Backend

- Check that the phone and backend computer are on the same network.
- Use the computer LAN IP, not `localhost`.
- Confirm Windows firewall or cloud firewall allows the backend port.
- From the phone browser, try opening `http://<computer-lan-ip>:8000/health`.
- If using Docker, confirm the container exposes port `8000`.

### Wrong Device Token

- Confirm the app token matches the backend expected token.
- Check for extra spaces before or after the token.
- Re-save settings and retry upload.
- Confirm backend logs show authentication failure rather than upload parsing failure.

### Cleartext HTTP Blocked

- Prefer HTTPS for remote servers.
- For local development, confirm the Android network security configuration or manifest allows the intended cleartext host.
- If using a LAN IP over `http://`, verify the debug build is configured to allow it.

### Android Foreground Service Permission Issue

- Confirm the app has microphone permission.
- Confirm notification permission is granted on Android 13 or later.
- Confirm the manifest includes foreground service microphone permissions.
- Test on a physical device because emulator and vendor ROM behavior can differ.

### Notification Not Showing

- Confirm notification permission is allowed.
- Check the system notification settings for the app.
- Confirm Do Not Disturb is not hiding notifications.
- Start recording again and watch for the persistent recording notification.

### Upload Fails

- Confirm the backend health endpoint works from the phone.
- Confirm the server URL has no trailing path such as `/api/v1`.
- Confirm the `.m4a` file exists and is non-empty.
- Check backend logs for request size, auth, or validation errors.
- Retry with a short recording under one minute.

### Transcript Empty

- Confirm upload completed and returned a backend session ID.
- Wait a few seconds and fetch transcript again.
- Confirm `ASR_PROVIDER=mock` for local testing.
- Check backend logs for processing failures.

### Analysis Not Ready Yet

- Fetch analysis again after a short wait.
- Confirm mock processing reached the analyzed status.
- Confirm `USE_DEEPSEEK=false` when no DeepSeek key is configured.
- Check backend logs for invalid analysis JSON, auth errors, or failed processing state.

## 10. Pass Criteria

- [ ] The app records only after explicit user action.
- [ ] Recording always shows a persistent foreground notification.
- [ ] Pause, resume, and stop work from both app and notification.
- [ ] A non-empty `.m4a` file is saved in app-private storage.
- [ ] Upload succeeds against the backend.
- [ ] Transcript, analysis, and daily review can be fetched with mock processing.
- [ ] No hidden recording, stealth recording, or phone-call recording behavior is present.
