from pathlib import Path


def test_upload_audio_session_saves_file_and_runs_mock_pipeline(
    client, auth_headers, test_settings
):
    response = client.post(
        "/api/v1/audio-sessions",
        headers=auth_headers,
        data={
            "device_id": "android_test",
            "started_at": "2026-06-25T09:30:12+08:00",
            "ended_at": "2026-06-25T09:32:12+08:00",
            "metadata": '{"scene":"channel","privacy_level":"work"}',
        },
        files={"audio": ("sample.m4a", b"fake-audio", "audio/mp4")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "queued"
    assert body["session_id"].startswith("session_20260625_093012_")

    session_response = client.get(
        f"/api/v1/audio-sessions/{body['session_id']}", headers=auth_headers
    )
    assert session_response.status_code == 200
    session = session_response.json()
    assert session["id"] == body["session_id"]
    assert session["device_id"] == "android_test"
    assert session["status"] == "analyzed"
    assert session["scene"] == "channel"
    assert session["privacy_level"] == "work"

    saved_files = list(Path(test_settings.storage_dir).rglob("*.m4a"))
    assert len(saved_files) == 1
    assert saved_files[0].read_bytes() == b"fake-audio"


def test_upload_creates_mock_transcript_and_analysis(client, auth_headers):
    upload_response = client.post(
        "/api/v1/audio-sessions",
        headers=auth_headers,
        data={
            "device_id": "android_test",
            "started_at": "2026-06-25T09:30:12+08:00",
            "ended_at": "2026-06-25T09:32:12+08:00",
        },
        files={"audio": ("sample.m4a", b"fake-audio", "audio/mp4")},
    )
    session_id = upload_response.json()["session_id"]

    transcript_response = client.get(
        f"/api/v1/audio-sessions/{session_id}/transcript", headers=auth_headers
    )
    assert transcript_response.status_code == 200
    transcript = transcript_response.json()
    assert transcript["session_id"] == session_id
    assert [segment["speaker_label"] for segment in transcript["segments"]] == [
        "我",
        "对方",
    ]
    assert "续保" in transcript["segments"][0]["text"]
    assert transcript["segments"][0]["start_ms"] == 0

    analysis_response = client.get(
        f"/api/v1/audio-sessions/{session_id}/analysis", headers=auth_headers
    )
    assert analysis_response.status_code == 200
    analysis = analysis_response.json()
    assert analysis["session_id"] == session_id
    assert analysis["summary"] == "模拟分析：本次沟通围绕续保推进和后续动作展开。"
    assert analysis["scores"]["goal_clarity"] == 8
    assert analysis["todos"][0]["task"] == "确认续保推进清单"


def test_upload_requires_device_token(client):
    response = client.post(
        "/api/v1/audio-sessions",
        data={
            "device_id": "android_test",
            "started_at": "2026-06-25T09:30:12+08:00",
            "ended_at": "2026-06-25T09:32:12+08:00",
        },
        files={"audio": ("sample.m4a", b"fake-audio", "audio/mp4")},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
