package com.xujianshuo.voicecoachrecorder.data

import android.content.Context
import com.xujianshuo.voicecoachrecorder.model.LocalSession
import org.json.JSONArray
import org.json.JSONObject

class SessionStore(context: Context) {
    private val prefs = context.getSharedPreferences("voice_coach_sessions", Context.MODE_PRIVATE)

    fun list(): List<LocalSession> {
        val raw = prefs.getString(KEY_SESSIONS, "[]") ?: "[]"
        val array = JSONArray(raw)
        return buildList {
            for (index in 0 until array.length()) {
                val item = array.getJSONObject(index)
                add(item.toLocalSession())
            }
        }.sortedByDescending { it.startedAtIso }
    }

    fun add(session: LocalSession) {
        save(list().filterNot { it.localId == session.localId } + session)
    }

    fun update(session: LocalSession) {
        save(list().map { if (it.localId == session.localId) session else it })
    }

    private fun save(sessions: List<LocalSession>) {
        val array = JSONArray()
        sessions.forEach { array.put(it.toJson()) }
        prefs.edit().putString(KEY_SESSIONS, array.toString()).apply()
    }

    private fun JSONObject.toLocalSession(): LocalSession {
        return LocalSession(
            localId = getString("localId"),
            filePath = getString("filePath"),
            startedAtIso = getString("startedAtIso"),
            endedAtIso = getString("endedAtIso"),
            backendSessionId = optString("backendSessionId").ifBlank { null },
            status = optString("status", "local"),
            transcript = optString("transcript", ""),
            analysis = optString("analysis", ""),
        )
    }

    private fun LocalSession.toJson(): JSONObject {
        return JSONObject()
            .put("localId", localId)
            .put("filePath", filePath)
            .put("startedAtIso", startedAtIso)
            .put("endedAtIso", endedAtIso)
            .put("backendSessionId", backendSessionId ?: "")
            .put("status", status)
            .put("transcript", transcript)
            .put("analysis", analysis)
    }

    private companion object {
        const val KEY_SESSIONS = "sessions"
    }
}
