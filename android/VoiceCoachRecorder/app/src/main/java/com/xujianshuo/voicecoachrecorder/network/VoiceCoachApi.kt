package com.xujianshuo.voicecoachrecorder.network

import com.xujianshuo.voicecoachrecorder.model.DailyReview
import com.xujianshuo.voicecoachrecorder.model.LocalSession
import com.xujianshuo.voicecoachrecorder.model.TranscriptSegment
import com.xujianshuo.voicecoachrecorder.model.UploadResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import org.json.JSONObject
import java.io.File

class VoiceCoachApi(
    private val client: OkHttpClient = OkHttpClient(),
) {
    suspend fun uploadSession(
        serverUrl: String,
        token: String,
        session: LocalSession,
    ): UploadResult = withContext(Dispatchers.IO) {
        val audioFile = File(session.filePath)
        require(audioFile.exists()) { "Recording file does not exist." }

        val metadata = JSONObject()
            .put("scene", "android_mvp")
            .put("privacy_level", "work")
            .toString()

        val body = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("device_id", android.os.Build.MODEL ?: "android_device")
            .addFormDataPart("started_at", session.startedAtIso)
            .addFormDataPart("ended_at", session.endedAtIso)
            .addFormDataPart("metadata", metadata)
            .addFormDataPart(
                "audio",
                audioFile.name,
                audioFile.asRequestBody("audio/mp4".toMediaType()),
            )
            .build()

        val request = Request.Builder()
            .url(buildApiUrl(serverUrl, "/api/v1/audio-sessions"))
            .addHeader("Authorization", "Bearer $token")
            .post(body)
            .build()

        client.newCall(request).execute().use { response ->
            val responseBody = response.body?.string().orEmpty()
            if (!response.isSuccessful) error("Upload failed: HTTP ${response.code} $responseBody")
            val json = JSONObject(responseBody)
            UploadResult(
                sessionId = json.getString("session_id"),
                status = json.optString("status", "queued"),
            )
        }
    }

    suspend fun fetchTranscript(
        serverUrl: String,
        token: String,
        sessionId: String,
    ): List<TranscriptSegment> = withContext(Dispatchers.IO) {
        val json = getJson(serverUrl, token, "/api/v1/audio-sessions/$sessionId/transcript")
        val segments = json.getJSONArray("segments")
        buildList {
            for (index in 0 until segments.length()) {
                val item = segments.getJSONObject(index)
                add(
                    TranscriptSegment(
                        startMs = item.optInt("start_ms"),
                        endMs = item.optInt("end_ms"),
                        speakerLabel = item.optString("speaker_label", "Speaker"),
                        text = item.optString("text"),
                    )
                )
            }
        }
    }

    suspend fun fetchAnalysis(
        serverUrl: String,
        token: String,
        sessionId: String,
    ): String = withContext(Dispatchers.IO) {
        val json = getJson(serverUrl, token, "/api/v1/audio-sessions/$sessionId/analysis")
        buildString {
            appendLine(json.optString("summary", ""))
            val scores = json.optJSONObject("scores")
            if (scores != null) appendLine("Scores: $scores")
            val todos = json.optJSONArray("todos")
            if (todos != null) appendLine("Todos: $todos")
        }.trim()
    }

    suspend fun fetchDailyReview(
        serverUrl: String,
        token: String,
        date: String,
    ): DailyReview = withContext(Dispatchers.IO) {
        val json = getJson(serverUrl, token, "/api/v1/daily-review?date=$date")
        val coaching = json.optJSONObject("coaching_summary")
        DailyReview(
            date = json.optString("date", date),
            summary = coaching?.optString("daily_summary")
                ?: "Valid sessions: ${json.optInt("valid_session_count")}",
        )
    }

    private fun getJson(serverUrl: String, token: String, path: String): JSONObject {
        val request = Request.Builder()
            .url(buildApiUrl(serverUrl, path))
            .addHeader("Authorization", "Bearer $token")
            .get()
            .build()
        client.newCall(request).execute().use { response ->
            val responseBody = response.body?.string().orEmpty()
            if (!response.isSuccessful) error("Request failed: HTTP ${response.code} $responseBody")
            return JSONObject(responseBody)
        }
    }
}
