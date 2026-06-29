package com.xujianshuo.voicecoachrecorder.data

import android.content.Context
import com.xujianshuo.voicecoachrecorder.model.RecorderSettings

class SettingsStore(context: Context) {
    private val prefs = context.getSharedPreferences("voice_coach_settings", Context.MODE_PRIVATE)

    fun load(): RecorderSettings {
        return RecorderSettings(
            serverUrl = prefs.getString(KEY_SERVER_URL, "") ?: "",
            deviceToken = prefs.getString(KEY_DEVICE_TOKEN, "") ?: "",
        )
    }

    fun save(settings: RecorderSettings) {
        prefs.edit()
            .putString(KEY_SERVER_URL, settings.serverUrl.trim())
            .putString(KEY_DEVICE_TOKEN, settings.deviceToken.trim())
            .apply()
    }

    private companion object {
        const val KEY_SERVER_URL = "server_url"
        const val KEY_DEVICE_TOKEN = "device_token"
    }
}
