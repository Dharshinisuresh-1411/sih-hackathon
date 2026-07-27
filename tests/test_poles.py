def test_valid_pole_can_be_created(client):
    res = client.post("/api/poles", json={
        "pole_number": "P-100", "ward": "Ward 1", "location": "Main Road",
    })
    assert res.status_code == 201
    assert res.get_json()["pole_number"] == "P-100"


def test_duplicate_pole_number_rejected(client, sample_pole):
    res = client.post("/api/poles", json={
        "pole_number": "P-001", "ward": "Ward 2", "location": "Somewhere",
    })
    assert res.status_code == 409
