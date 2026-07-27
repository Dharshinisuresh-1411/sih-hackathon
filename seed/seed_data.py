"""
Seed the database with sample data:
  ~25 poles, 5 electricians, ~40 complaints (some poles deliberately
  repeat-offenders), a mix of OPEN / ASSIGNED / IN_PROGRESS / CLOSED, and
  work records for assigned/closed complaints.

Run with:
    python seed/seed_data.py
"""
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import db
from models.pole import Pole
from models.electrician import Electrician
from models.complaint import Complaint
from models.work_record import WorkRecord

random.seed(42)

WARDS = ["Ward 1", "Ward 2", "Ward 3", "Ward 4", "Ward 5"]
LOCATIONS = [
    "Main Road", "Bus Stop", "Temple Road", "School Street", "Market Road",
    "Panchayat Office Road", "Lake View Road", "Cross Street", "Bridge Road",
    "Hospital Road", "Government School Road", "Water Tank Road", "New Colony",
    "Old Colony", "Railway Gate Road",
]

ELECTRICIANS = [
    ("Murugan S", "9840012345", True),
    ("Kumar R", "9840012346", True),
    ("Selvam P", "9840012347", True),
    ("Anitha K", "9840012348", True),
    ("Ravi Shankar", "9840012349", False),  # inactive, to demonstrate validation
]

DESCRIPTIONS = [
    "Light not working since last night",
    "Light flickering continuously",
    "Pole light stays off after 9 PM",
    "Bulb fused, completely dark",
    "Light comes on only during daytime",
    "Wire hanging loose near the pole",
    "Light very dim, needs replacement",
    "No light for the past 3 days",
]

REPAIR_NOTES = [
    ("Replaced damaged LED driver and checked wiring.", "LED Driver"),
    ("Replaced fused bulb with new LED bulb.", "LED Bulb"),
    ("Fixed loose wiring connection at the pole base.", "Wiring"),
    ("Replaced photocell sensor causing daytime operation.", "Photocell Sensor"),
    ("Cleaned connector and tightened terminal block.", "Terminal Block"),
]


def build_poles():
    poles = []
    pole_no = 1
    for ward in WARDS:
        for _ in range(5):  # 5 wards x 5 = 25 poles
            location = random.choice(LOCATIONS)
            status = random.choices(
                [Pole.STATUS_WORKING, Pole.STATUS_DARK, Pole.STATUS_UNDER_REPAIR,
                 Pole.STATUS_MAINTENANCE_REQUIRED],
                weights=[70, 12, 10, 8],
            )[0]
            poles.append(Pole(
                pole_number=f"P-{pole_no:03d}",
                ward=ward,
                location=location,
                status=status,
                created_at=datetime.utcnow() - timedelta(days=random.randint(60, 400)),
            ))
            pole_no += 1
    return poles


def random_recent_datetime(max_days_back=330):
    return datetime.utcnow() - timedelta(
        days=random.randint(0, max_days_back), hours=random.randint(0, 23)
    )


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ---- Poles ----
        poles = build_poles()
        db.session.add_all(poles)
        db.session.commit()

        # ---- Electricians ----
        electricians = [Electrician(name=n, phone=p, is_active=a) for n, p, a in ELECTRICIANS]
        db.session.add_all(electricians)
        db.session.commit()
        active_electricians = [e for e in electricians if e.is_active]

        # ---- Complaints ----
        # Deliberately make P-002, P-005 (ward 1/2 area) and a couple of others
        # repeat offenders by giving them extra complaint counts.
        repeat_offender_numbers = {"P-002": 8, "P-005": 6, "P-010": 4, "P-015": 3}

        complaint_count = 0
        target_total = 40

        # First, force the repeat-offender poles to get their counts.
        for pole_number, count in repeat_offender_numbers.items():
            pole = next(p for p in poles if p.pole_number == pole_number)
            for _ in range(count):
                complaint_count += 1
                created = random_recent_datetime()
                status = random.choices(
                    [Complaint.STATUS_OPEN, Complaint.STATUS_ASSIGNED,
                     Complaint.STATUS_IN_PROGRESS, Complaint.STATUS_CLOSED],
                    weights=[15, 15, 10, 60],
                )[0]
                c = Complaint(
                    pole_id=pole.id,
                    caller_name=random.choice(["Ramesh", "Priya", "Suresh", "Lakshmi", "Ganesh", "Meena"]),
                    caller_phone=f"98{random.randint(10000000, 99999999)}",
                    description=random.choice(DESCRIPTIONS),
                    status=status,
                    created_at=created,
                    updated_at=created,
                )
                db.session.add(c)
                db.session.flush()

                if status != Complaint.STATUS_OPEN:
                    electrician = random.choice(active_electricians)
                    wr = WorkRecord(
                        complaint_id=c.id,
                        electrician_id=electrician.id,
                        assigned_by="Panchayat Clerk",
                        assigned_at=created + timedelta(hours=random.randint(1, 12)),
                    )
                    if status == Complaint.STATUS_CLOSED:
                        note, item = random.choice(REPAIR_NOTES)
                        wr.closed_by = electrician.name
                        wr.closed_at = created + timedelta(days=random.randint(1, 3))
                        wr.repair_note = note
                        wr.replaced_item = item
                    db.session.add(wr)

        # Fill remaining complaints spread across other poles, ensuring at
        # most ONE currently-open complaint per pole (keeps demo consistent
        # with the "no duplicate open complaints" rule).
        other_poles = [p for p in poles if p.pole_number not in repeat_offender_numbers]
        pole_has_open = set()

        while complaint_count < target_total:
            pole = random.choice(other_poles)
            complaint_count += 1
            created = random_recent_datetime()

            if pole.pole_number in pole_has_open:
                status = random.choice(
                    [Complaint.STATUS_ASSIGNED, Complaint.STATUS_IN_PROGRESS, Complaint.STATUS_CLOSED]
                )
            else:
                status = random.choices(
                    [Complaint.STATUS_OPEN, Complaint.STATUS_ASSIGNED,
                     Complaint.STATUS_IN_PROGRESS, Complaint.STATUS_CLOSED],
                    weights=[25, 15, 10, 50],
                )[0]
                if status == Complaint.STATUS_OPEN:
                    pole_has_open.add(pole.pole_number)

            c = Complaint(
                pole_id=pole.id,
                caller_name=random.choice(["Ramesh", "Priya", "Suresh", "Lakshmi", "Ganesh", "Meena"]),
                caller_phone=f"98{random.randint(10000000, 99999999)}",
                description=random.choice(DESCRIPTIONS),
                status=status,
                created_at=created,
                updated_at=created,
            )
            db.session.add(c)
            db.session.flush()

            if status != Complaint.STATUS_OPEN:
                electrician = random.choice(active_electricians)
                wr = WorkRecord(
                    complaint_id=c.id,
                    electrician_id=electrician.id,
                    assigned_by="Panchayat Clerk",
                    assigned_at=created + timedelta(hours=random.randint(1, 12)),
                )
                if status == Complaint.STATUS_CLOSED:
                    note, item = random.choice(REPAIR_NOTES)
                    wr.closed_by = electrician.name
                    wr.closed_at = created + timedelta(days=random.randint(1, 3))
                    wr.repair_note = note
                    wr.replaced_item = item
                db.session.add(wr)

        db.session.commit()
        print(f"Seed complete: {Pole.query.count()} poles, "
              f"{Electrician.query.count()} electricians, "
              f"{Complaint.query.count()} complaints.")


if __name__ == "__main__":
    seed()
