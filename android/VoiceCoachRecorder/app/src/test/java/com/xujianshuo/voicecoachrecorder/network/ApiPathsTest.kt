package com.xujianshuo.voicecoachrecorder.network

import org.junit.Assert.assertEquals
import org.junit.Test

class ApiPathsTest {
    @Test
    fun buildApiUrlJoinsServerAndPathWithoutDoubleSlashes() {
        assertEquals(
            "https://example.com/api/v1/health",
            buildApiUrl("https://example.com/", "/api/v1/health"),
        )
    }

    @Test
    fun buildApiUrlTrimsWhitespace() {
        assertEquals(
            "http://10.0.2.2:8000/api/v1/audio-sessions",
            buildApiUrl(" http://10.0.2.2:8000 ", "api/v1/audio-sessions"),
        )
    }
}
