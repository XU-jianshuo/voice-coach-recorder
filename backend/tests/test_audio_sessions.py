from pathlib import Path


def test_upload_audio_session_saves_file_and_creates_queued_session(
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
    assert session["status"] == "queued"
    assert session["scene"] == "channel"
    assert session["privacy_level"] == "work"

    saved_files = list(Path(test_settings.storage_dir).rglob("*.m4a"))
    assert len(saved_files) == 1
    assert saved_files[0].read_bytes() == b"fake-audio"


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


def test_transcript_endpoint_returns_empty_segments_for_queued_session(
    client, auth_headers
):
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

    response = client.get(
        f"/api/v1/audio-sessions/{session_id}/transcript", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json() == {"session_id": session_id, "segments": []}


def test_analysis_endpoint_returns_404_until_analysis_exists(client, auth_headers):
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

    response = client.get(
        f"/api/v1/audio-sessions/{session_id}/analysis", headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "analysis_not_found"
