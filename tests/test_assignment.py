from models import db
from models.pole import Pole


def create_complaint(client):
    res = client.post("/api/complaints", json={
        "pole_number": "P-001", "caller_name": "Ramesh",
        "caller_phone": "9840011111", "description": "Light not working",
    })
    return res.get_json()["complaint"]


def test_complaint_can_be_assigned_to_active_electrician(client, sample_pole, active_electrician):
    complaint = create_complaint(client)
    res = client.post(f"/api/complaints/{complaint['id']}/assign", json={
        "electrician_id": active_electrician.id,
    })
    assert res.status_code == 200
    assert res.get_json()["status"] == "ASSIGNED"


def test_inactive_electrician_cannot_be_assigned(client, sample_pole, inactive_electrician):
    complaint = create_complaint(client)
    res = client.post(f"/api/complaints/{complaint['id']}/assign", json={
        "electrician_id": inactive_electrician.id,
    })
    assert res.status_code == 400
    assert "inactive" in res.get_json()["error"].lower()


def test_pole_status_updates_after_assignment_and_closure(client, sample_pole, active_electrician):
    complaint = create_complaint(client)

    assign_res = client.post(f"/api/complaints/{complaint['id']}/assign", json={
        "electrician_id": active_electrician.id,
    })
    assert assign_res.status_code == 200

    close_res = client.post(f"/api/complaints/{complaint['id']}/close", json={
        "closed_by": "Murugan S",
        "repair_note": "Replaced LED driver",
        "replaced_item": "LED Driver",
        "version": assign_res.get_json()["version"],
    })
    assert close_res.status_code == 200

    updated_pole = db.session.get(Pole, sample_pole.id)
    assert updated_pole.status == Pole.STATUS_WORKING
