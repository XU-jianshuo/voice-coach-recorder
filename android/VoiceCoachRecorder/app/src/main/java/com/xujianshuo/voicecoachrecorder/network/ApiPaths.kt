package com.xujianshuo.voicecoachrecorder.network

fun buildApiUrl(serverUrl: String, path: String): String {
    return "${serverUrl.trim().trimEnd('/')}/${path.trimStart('/')}"
}
