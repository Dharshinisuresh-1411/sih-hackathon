def base_payload(pole_number="P-001"):
    return {
        "pole_number": pole_number,
        "caller_name": "Ramesh",
        "caller_phone": "9840011111",
        "description": "Light not working",
    }


def test_unknown_pole_complaint_is_rejected(client):
    res = client.post("/api/complaints", json=base_payload("P-999"))
    assert res.status_code == 404


def test_valid_complaint_created(client, sample_pole):
    res = client.post("/api/complaints", json=base_payload())
    assert res.status_code == 201
    body = res.get_json()
    assert body["duplicate"] is False
    assert body["complaint"]["status"] == "OPEN"


def test_complaint_remarks_are_saved_and_returned(client, sample_pole):
    payload = base_payload()
    payload["remarks"] = "Please inspect the pole before dusk."

    res = client.post("/api/complaints", json=payload)
    assert res.status_code == 201
    body = res.get_json()
    assert body["complaint"]["remarks"] == payload["remarks"]

    get_res = client.get(f"/api/complaints/{body['complaint']['id']}")
    assert get_res.status_code == 200
    assert get_res.get_json()["remarks"] == payload["remarks"]


def test_existing_open_complaint_is_detected(client, sample_pole):
    first = client.post("/api/complaints", json=base_payload())
    assert first.status_code == 201

    second = client.post("/api/complaints", json=base_payload())
    assert second.status_code == 200
    body = second.get_json()
    assert body["duplicate"] is True
    assert body["existing_complaint"]["id"] == first.get_json()["complaint"]["id"]


def test_keyword_search_returns_matching_complaints_only(client, sample_pole):
    client.post(
        "/api/complaints",
        json={
            **base_payload(),
            "description": "Broken streetlight near market",
            "remarks": "Follow-up needed",
        },
    )
    client.post(
        "/api/complaints",
        json={
            **base_payload("P-002"),
            "description": "Water leak on road",
            "remarks": "No action",
        },
    )

    res = client.get("/api/complaints?q=market")
    assert res.status_code == 200
    body = res.get_json()
    assert len(body) == 1
    assert body[0]["description"] == "Broken streetlight near market"
    assert body[0]["remarks"] == "Follow-up needed"


def test_keyword_search_returns_empty_for_no_matches(client, sample_pole):
    client.post("/api/complaints", json=base_payload())

    res = client.get("/api/complaints?q=zzzz-no-match")
    assert res.status_code == 200
    assert res.get_json() == []


def test_open_complaints_by_ward(client, sample_pole):
    client.post("/api/complaints", json=base_payload())
    res = client.get("/api/reports/open-by-ward")
    assert res.status_code == 200
    wards = {row["ward"]: row["open_complaints"] for row in res.get_json()}
    assert wards.get("Ward 1") == 1
