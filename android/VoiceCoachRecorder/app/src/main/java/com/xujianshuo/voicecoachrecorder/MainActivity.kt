package com.xujianshuo.voicecoachrecorder

import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.xujianshuo.voicecoachrecorder.data.SessionStore
import com.xujianshuo.voicecoachrecorder.data.SettingsStore
import com.xujianshuo.voicecoachrecorder.model.LocalSession
import com.xujianshuo.voicecoachrecorder.model.RecorderSettings
import com.xujianshuo.voicecoachrecorder.network.VoiceCoachApi
import com.xujianshuo.voicecoachrecorder.recording.RecordingService
import kotlinx.coroutines.launch
import java.io.File
import java.time.LocalDate
import java.util.UUID

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    VoiceCoachApp()
                }
            }
        }
    }
}

@Composable
private fun VoiceCoachApp() {
    val context = LocalContext.current
    val settingsStore = remember { SettingsStore(context) }
    val sessionStore = remember { SessionStore(context) }
    val api = remember { VoiceCoachApi() }
    val scope = rememberCoroutineScope()

    var settings by remember { mutableStateOf(settingsStore.load()) }
    var isRecording by remember { mutableStateOf(false) }
    var isPaused by remember { mutableStateOf(false) }
    var statusMessage by remember { mutableStateOf("Ready") }
    var selectedSession by remember { mutableStateOf<LocalSession?>(null) }
    var dailyReview by remember { mutableStateOf("") }
    val sessions = remember { mutableStateListOf<LocalSession>() }

    fun reloadSessions() {
        sessions.clear()
        sessions.addAll(sessionStore.list())
        selectedSession = selectedSession?.let { current ->
            sessions.firstOrNull { it.localId == current.localId }
        }
    }

    fun saveSession(session: LocalSession) {
        sessionStore.update(session)
        reloadSessions()
        selectedSession = session
    }

    LaunchedEffect(Unit) {
        reloadSessions()
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { result ->
        val micGranted = result[Manifest.permission.RECORD_AUDIO] == true
        val notificationGranted = if (Build.VERSION.SDK_INT >= 33) {
            result[Manifest.permission.POST_NOTIFICATIONS] == true
        } else {
            true
        }
        if (micGranted && notificationGranted) {
            ContextCompat.startForegroundService(
                context,
                RecordingService.intent(context, RecordingService.ACTION_START),
            )
            isRecording = true
            isPaused = false
            statusMessage = "Recording"
        } else {
            statusMessage = "Microphone and notification permissions are required."
        }
    }

    DisposableEffect(Unit) {
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                val filePath = intent.getStringExtra(RecordingService.EXTRA_FILE_PATH) ?: return
                val startedAt = intent.getStringExtra(RecordingService.EXTRA_STARTED_AT) ?: return
                val endedAt = intent.getStringExtra(RecordingService.EXTRA_ENDED_AT) ?: return
                val session = LocalSession(
                    localId = UUID.randomUUID().toString(),
                    filePath = filePath,
                    startedAtIso = startedAt,
                    endedAtIso = endedAt,
                )
                sessionStore.add(session)
                reloadSessions()
                selectedSession = session
                isRecording = false
                isPaused = false
                statusMessage = "Saved ${File(filePath).name}"
            }
        }
        val filter = IntentFilter(RecordingService.ACTION_RECORDING_COMPLETED)
        ContextCompat.registerReceiver(
            context,
            receiver,
            filter,
            ContextCompat.RECEIVER_NOT_EXPORTED,
        )
        onDispose {
            context.unregisterReceiver(receiver)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Voice Coach Recorder", style = MaterialTheme.typography.headlineSmall)
        SettingsPanel(settings = settings, onSave = {
            settings = it
            settingsStore.save(it)
            statusMessage = "Settings saved"
        })
        RecordingControls(
            isRecording = isRecording,
            isPaused = isPaused,
            status = statusMessage,
            onStart = {
                val permissions = buildList {
                    add(Manifest.permission.RECORD_AUDIO)
                    if (Build.VERSION.SDK_INT >= 33) add(Manifest.permission.POST_NOTIFICATIONS)
                }.toTypedArray()
                permissionLauncher.launch(permissions)
            },
            onPause = {
                context.startService(RecordingService.intent(context, RecordingService.ACTION_PAUSE))
                isPaused = true
                statusMessage = "Paused"
            },
            onResume = {
                context.startService(RecordingService.intent(context, RecordingService.ACTION_RESUME))
                isPaused = false
                statusMessage = "Recording"
            },
            onStop = {
                context.startService(RecordingService.intent(context, RecordingService.ACTION_STOP))
                statusMessage = "Stopping"
            },
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = {
                scope.launch {
                    runCatching {
                        api.fetchDailyReview(
                            settings.serverUrl,
                            settings.deviceToken,
                            LocalDate.now().toString(),
                        )
                    }.onSuccess {
                        dailyReview = "${it.date}\n${it.summary}"
                    }.onFailure {
                        dailyReview = it.message.orEmpty()
                    }
                }
            }) {
                Text("Daily Review")
            }
        }
        if (dailyReview.isNotBlank()) {
            Text(dailyReview, style = MaterialTheme.typography.bodyMedium)
        }
        SessionList(
            sessions = sessions,
            selected = selectedSession,
            onSelect = { selectedSession = it },
        )
        selectedSession?.let { session ->
            SessionDetail(
                settings = settings,
                api = api,
                session = session,
                onSessionChanged = ::saveSession,
                onStatus = { statusMessage = it },
            )
        }
    }
}

@Composable
private fun SettingsPanel(
    settings: RecorderSettings,
    onSave: (RecorderSettings) -> Unit,
) {
    var serverUrl by remember(settings.serverUrl) { mutableStateOf(settings.serverUrl) }
    var deviceToken by remember(settings.deviceToken) { mutableStateOf(settings.deviceToken) }

    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Backend Settings", fontWeight = FontWeight.SemiBold)
            OutlinedTextField(
                value = serverUrl,
                onValueChange = { serverUrl = it },
                label = { Text("Server URL") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            OutlinedTextField(
                value = deviceToken,
                onValueChange = { deviceToken = it },
                label = { Text("Device token") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Button(onClick = { onSave(RecorderSettings(serverUrl, deviceToken)) }) {
                Text("Save")
            }
        }
    }
}

@Composable
private fun RecordingControls(
    isRecording: Boolean,
    isPaused: Boolean,
    status: String,
    onStart: () -> Unit,
    onPause: () -> Unit,
    onResume: () -> Unit,
    onStop: () -> Unit,
) {
    Card {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(status, fontWeight = FontWeight.SemiBold)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = onStart, enabled = !isRecording) {
                    Text("Start")
                }
                Button(onClick = if (isPaused) onResume else onPause, enabled = isRecording) {
                    Text(if (isPaused) "Resume" else "Pause")
                }
                Button(onClick = onStop, enabled = isRecording) {
                    Text("Stop")
                }
            }
        }
    }
}

@Composable
private fun SessionList(
    sessions: List<LocalSession>,
    selected: LocalSession?,
    onSelect: (LocalSession) -> Unit,
) {
    Text("Sessions", fontWeight = FontWeight.SemiBold)
    LazyColumn(
        modifier = Modifier
            .fillMaxWidth()
            .height(180.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        items(sessions, key = { it.localId }) { session ->
            Card(
                onClick = { onSelect(session) },
                colors = CardDefaults.cardColors(
                    containerColor = if (selected?.localId == session.localId) {
                        MaterialTheme.colorScheme.primaryContainer
                    } else {
                        MaterialTheme.colorScheme.surfaceVariant
                    },
                ),
            ) {
                Column(modifier = Modifier.padding(10.dp)) {
                    Text(session.startedAtIso)
                    Text(session.status, style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}

@Composable
private fun SessionDetail(
    settings: RecorderSettings,
    api: VoiceCoachApi,
    session: LocalSession,
    onSessionChanged: (LocalSession) -> Unit,
    onStatus: (String) -> Unit,
) {
    val scope = rememberCoroutineScope()

    Card {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Session Detail", fontWeight = FontWeight.SemiBold)
            Text(File(session.filePath).name, style = MaterialTheme.typography.bodySmall)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = {
                    scope.launch {
                        runCatching {
                            api.uploadSession(settings.serverUrl, settings.deviceToken, session)
                        }.onSuccess { result ->
                            onSessionChanged(
                                session.copy(
                                    backendSessionId = result.sessionId,
                                    status = result.status,
                                )
                            )
                            onStatus("Uploaded ${result.sessionId}")
                        }.onFailure {
                            onStatus(it.message.orEmpty())
                        }
                    }
                }) {
                    Text("Upload")
                }
                Button(
                    enabled = session.backendSessionId != null,
                    onClick = {
                        scope.launch {
                            val backendId = session.backendSessionId ?: return@launch
                            runCatching {
                                api.fetchTranscript(settings.serverUrl, settings.deviceToken, backendId)
                            }.onSuccess { segments ->
                                val transcript = segments.joinToString("\n") {
                                    "[${it.speakerLabel}] ${it.text}"
                                }
                                onSessionChanged(session.copy(transcript = transcript))
                                onStatus("Transcript loaded")
                            }.onFailure {
                                onStatus(it.message.orEmpty())
                            }
                        }
                    },
                ) {
                    Text("Transcript")
                }
                Button(
                    enabled = session.backendSessionId != null,
                    onClick = {
                        scope.launch {
                            val backendId = session.backendSessionId ?: return@launch
                            runCatching {
                                api.fetchAnalysis(settings.serverUrl, settings.deviceToken, backendId)
                            }.onSuccess { analysis ->
                                onSessionChanged(session.copy(analysis = analysis))
                                onStatus("Analysis loaded")
                            }.onFailure {
                                onStatus(it.message.orEmpty())
                            }
                        }
                    },
                ) {
                    Text("Analysis")
                }
            }
            if (session.backendSessionId != null) {
                Text("Backend: ${session.backendSessionId}", style = MaterialTheme.typography.bodySmall)
            }
            if (session.transcript.isNotBlank()) {
                Text("Transcript", fontWeight = FontWeight.SemiBold)
                Text(session.transcript)
            }
            if (session.analysis.isNotBlank()) {
                Spacer(Modifier.height(4.dp))
                Text("Analysis", fontWeight = FontWeight.SemiBold)
                Text(session.analysis)
            }
        }
    }
}
