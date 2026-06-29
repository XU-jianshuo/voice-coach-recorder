package com.xujianshuo.voicecoachrecorder.model

data class RecorderSettings(
    val serverUrl: String = "",
    val deviceToken: String = "",
)

data class LocalSession(
    val localId: String,
    val filePath: String,
    val startedAtIso: String,
    val endedAtIso: String,
    val backendSessionId: String? = null,
    val status: String = "local",
    val transcript: String = "",
    val analysis: String = "",
)

data class TranscriptSegment(
    val startMs: Int,
    val endMs: Int,
    val speakerLabel: String,
    val text: String,
)

data class UploadResult(
    val sessionId: String,
    val status: String,
)

data class DailyReview(
    val date: String,
    val summary: String,
)
