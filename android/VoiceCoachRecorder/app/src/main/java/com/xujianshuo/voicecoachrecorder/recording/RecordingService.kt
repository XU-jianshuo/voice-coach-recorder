package com.xujianshuo.voicecoachrecorder.recording

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.media.MediaRecorder
import android.os.Build
import android.os.Environment
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.xujianshuo.voicecoachrecorder.MainActivity
import com.xujianshuo.voicecoachrecorder.R
import java.io.File
import java.time.Instant
import java.time.format.DateTimeFormatter
import java.util.UUID

class RecordingService : Service() {
    private var recorder: MediaRecorder? = null
    private var outputFile: File? = null
    private var startedAt: Instant? = null
    private var isPaused: Boolean = false

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startRecording()
            ACTION_PAUSE -> pauseRecording()
            ACTION_RESUME -> resumeRecording()
            ACTION_STOP -> stopRecording()
        }
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        recorder?.release()
        recorder = null
        super.onDestroy()
    }

    private fun startRecording() {
        if (recorder != null) return

        val start = Instant.now()
        startedAt = start
        outputFile = createOutputFile(start)
        val currentOutput = requireNotNull(outputFile)

        recorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(this)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }.apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setAudioEncodingBitRate(128_000)
            setAudioSamplingRate(44_100)
            setOutputFile(currentOutput.absolutePath)
            prepare()
            start()
        }

        isPaused = false
        startForeground(NOTIFICATION_ID, buildNotification("Recording"))
    }

    private fun pauseRecording() {
        val activeRecorder = recorder ?: return
        if (!isPaused) {
            activeRecorder.pause()
            isPaused = true
            notifyStatus("Paused")
        }
    }

    private fun resumeRecording() {
        val activeRecorder = recorder ?: return
        if (isPaused) {
            activeRecorder.resume()
            isPaused = false
            notifyStatus("Recording")
        }
    }

    private fun stopRecording() {
        val activeRecorder = recorder ?: return
        val end = Instant.now()
        try {
            activeRecorder.stop()
        } finally {
            activeRecorder.release()
            recorder = null
            stopForeground(STOP_FOREGROUND_REMOVE)
        }
        broadcastCompleted(end)
        stopSelf()
    }

    private fun broadcastCompleted(endedAt: Instant) {
        val file = outputFile ?: return
        val start = startedAt ?: return
        sendBroadcast(
            Intent(ACTION_RECORDING_COMPLETED)
                .setPackage(packageName)
                .putExtra(EXTRA_FILE_PATH, file.absolutePath)
                .putExtra(EXTRA_STARTED_AT, DateTimeFormatter.ISO_INSTANT.format(start))
                .putExtra(EXTRA_ENDED_AT, DateTimeFormatter.ISO_INSTANT.format(endedAt))
        )
    }

    private fun createOutputFile(start: Instant): File {
        val directory = File(
            getExternalFilesDir(Environment.DIRECTORY_MUSIC),
            "recordings",
        )
        directory.mkdirs()
        return File(directory, "voice_${start.toEpochMilli()}_${UUID.randomUUID()}.m4a")
    }

    private fun notifyStatus(status: String) {
        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(NOTIFICATION_ID, buildNotification(status))
    }

    private fun buildNotification(status: String): Notification {
        val contentIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val stopIntent = PendingIntent.getService(
            this,
            1,
            Intent(this, RecordingService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val pauseAction = if (isPaused) ACTION_RESUME else ACTION_PAUSE
        val pauseTitle = if (isPaused) "Resume" else "Pause"
        val pauseIntent = PendingIntent.getService(
            this,
            2,
            Intent(this, RecordingService::class.java).setAction(pauseAction),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_mic)
            .setContentTitle("Voice Coach Recorder")
            .setContentText(status)
            .setContentIntent(contentIntent)
            .setOngoing(true)
            .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
            .addAction(R.drawable.ic_mic, pauseTitle, pauseIntent)
            .addAction(R.drawable.ic_mic, "Stop", stopIntent)
            .build()
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            getString(R.string.recording_channel_name),
            NotificationManager.IMPORTANCE_LOW,
        )
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    companion object {
        const val ACTION_START = "com.xujianshuo.voicecoachrecorder.START_RECORDING"
        const val ACTION_PAUSE = "com.xujianshuo.voicecoachrecorder.PAUSE_RECORDING"
        const val ACTION_RESUME = "com.xujianshuo.voicecoachrecorder.RESUME_RECORDING"
        const val ACTION_STOP = "com.xujianshuo.voicecoachrecorder.STOP_RECORDING"
        const val ACTION_RECORDING_COMPLETED =
            "com.xujianshuo.voicecoachrecorder.RECORDING_COMPLETED"

        const val EXTRA_FILE_PATH = "file_path"
        const val EXTRA_STARTED_AT = "started_at"
        const val EXTRA_ENDED_AT = "ended_at"

        private const val CHANNEL_ID = "voice_coach_recording"
        private const val NOTIFICATION_ID = 1001

        fun intent(context: Context, action: String): Intent {
            return Intent(context, RecordingService::class.java).setAction(action)
        }
    }
}
