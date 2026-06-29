def test_create_and_list_speaker_profiles(client, auth_headers):
    create_response = client.post(
        "/api/v1/speaker-profiles",
        headers=auth_headers,
        json={"display_name": "我", "type": "self"},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"].startswith("speaker_")
    assert created["display_name"] == "我"
    assert created["type"] == "self"

    list_response = client.get("/api/v1/speaker-profiles", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"] == [created]


def test_speaker_profile_rejects_invalid_type(client, auth_headers):
    response = client.post(
        "/api/v1/speaker-profiles",
        headers=auth_headers,
        json={"display_name": "张三", "type": "customer"},
    )

    assert response.status_code == 422


def test_update_segment_speaker_label_and_apply_to_session(client, auth_headers):
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
    transcript = client.get(
        f"/api/v1/audio-sessions/{session_id}/transcript", headers=auth_headers
    ).json()
    target_segment = transcript["segments"][1]

    response = client.patch(
        f"/api/v1/transcript-segments/{target_segment['id']}/speaker",
        headers=auth_headers,
        json={
            "speaker_label": "疑似张三",
            "speaker_profile_id": None,
            "apply_to_session": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "segment_id": target_segment["id"],
        "speaker_label": "疑似张三",
        "updated": True,
    }
    updated = client.get(
        f"/api/v1/audio-sessions/{session_id}/transcript", headers=auth_headers
    ).json()
    matching_segments = [
        segment
        for segment in updated["segments"]
        if segment["speaker_id"] == target_segment["speaker_id"]
    ]
    assert {segment["speaker_label"] for segment in matching_segments} == {"疑似张三"}


def test_update_segment_speaker_profile_applies_to_matching_session_speakers(
    client, auth_headers
):
    profile_response = client.post(
        "/api/v1/speaker-profiles",
        headers=auth_headers,
        json={"display_name": "我", "type": "self"},
    )
    profile_id = profile_response.json()["id"]
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
    transcript = client.get(
        f"/api/v1/audio-sessions/{session_id}/transcript", headers=auth_headers
    ).json()
    target_segment = transcript["segments"][0]

    response = client.patch(
        f"/api/v1/transcript-segments/{target_segment['id']}/speaker",
        headers=auth_headers,
        json={
            "speaker_label": "我",
            "speaker_profile_id": profile_id,
            "apply_to_session": True,
        },
    )

    assert response.status_code == 200
    updated = client.get(
        f"/api/v1/audio-sessions/{session_id}/transcript", headers=auth_headers
    ).json()
    updated_segment = [
        segment for segment in updated["segments"] if segment["id"] == target_segment["id"]
    ][0]
    assert updated_segment["speaker_id"] == profile_id
    assert updated_segment["speaker_label"] == "我"
