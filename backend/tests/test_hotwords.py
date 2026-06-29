def test_hotwords_are_seeded_by_default(client, auth_headers):
    response = client.get("/api/v1/hotwords", headers=auth_headers)

    assert response.status_code == 200
    texts = [item["text"] for item in response.json()["items"]]
    assert "车险" in texts
    assert "驾意险" in texts
    assert "续保率" in texts
    assert "通报" in texts


def test_create_and_delete_hotword(client, auth_headers):
    create_response = client.post(
        "/api/v1/hotwords",
        headers=auth_headers,
        json={"text": "新渠道词", "category": "business", "weight": 9},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["text"] == "新渠道词"
    assert created["weight"] == 9

    list_response = client.get("/api/v1/hotwords", headers=auth_headers)
    assert "新渠道词" in [item["text"] for item in list_response.json()["items"]]

    delete_response = client.delete(
        f"/api/v1/hotwords/{created['id']}", headers=auth_headers
    )
    assert delete_response.status_code == 204

    after_delete = client.get("/api/v1/hotwords", headers=auth_headers)
    assert "新渠道词" not in [item["text"] for item in after_delete.json()["items"]]
