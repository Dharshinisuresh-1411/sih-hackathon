def setup_assigned_complaint(client, active_electrician):
    c = client.post("/api/complaints", json={
        "pole_number": "P-001", "caller_name": "Ramesh",
        "caller_phone": "9840011111", "description": "Light not working",
    }).get_json()["complaint"]

    assigned = client.post(f"/api/complaints/{c['id']}/assign", json={
        "electrician_id": active_electrician.id,
    }).get_json()
    return assigned


def test_complaint_can_be_closed(client, sample_pole, active_electrician):
    complaint = setup_assigned_complaint(client, active_electrician)
    res = client.post(f"/api/complaints/{complaint['id']}/close", json={
        "closed_by": "Murugan S", "repair_note": "Replaced LED driver",
        "replaced_item": "LED Driver", "version": complaint["version"],
    })
    assert res.status_code == 200
    assert res.get_json()["complaint"]["status"] == "CLOSED"


def test_closed_complaint_cannot_be_closed_again(client, sample_pole, active_electrician):
    complaint = setup_assigned_complaint(client, active_electrician)
    first = client.post(f"/api/complaints/{complaint['id']}/close", json={
        "closed_by": "Murugan S", "repair_note": "Replaced LED driver",
        "version": complaint["version"],
    })
    assert first.status_code == 200

    # Second attempt uses the SAME (now stale) version -> must be rejected.
    second = client.post(f"/api/complaints/{complaint['id']}/close", json={
        "closed_by": "Kumar R", "repair_note": "Also replaced LED driver",
        "version": complaint["version"],
    })
    assert second.status_code == 409
    assert "already been closed" in second.get_json()["error"].lower()
