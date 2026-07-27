from datetime import datetime
from . import db


class Complaint(db.Model):
    __tablename__ = "complaints"

    STATUS_OPEN = "OPEN"
    STATUS_ASSIGNED = "ASSIGNED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_CLOSED = "CLOSED"

    VALID_STATUSES = [STATUS_OPEN, STATUS_ASSIGNED, STATUS_IN_PROGRESS, STATUS_CLOSED]

    # Allowed forward transitions. Anything not listed here is rejected.
    ALLOWED_TRANSITIONS = {
        STATUS_OPEN: [STATUS_ASSIGNED],
        STATUS_ASSIGNED: [STATUS_IN_PROGRESS, STATUS_CLOSED],
        STATUS_IN_PROGRESS: [STATUS_CLOSED],
        STATUS_CLOSED: [],  # terminal state
    }

    id = db.Column(db.Integer, primary_key=True)
    pole_id = db.Column(db.Integer, db.ForeignKey("poles.id"), nullable=False, index=True)
    caller_name = db.Column(db.String(100), nullable=False)
    caller_phone = db.Column(db.String(15), nullable=False)
    description = db.Column(db.Text, nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=STATUS_OPEN, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Optimistic-locking version counter. Every update that changes state
    # must increment this. Used to safely handle FAILURE CASE 1 (two staff
    # closing the same complaint at the same time).
    version = db.Column(db.Integer, nullable=False, default=1)

    work_record = db.relationship(
        "WorkRecord", backref="complaint", uselist=False, cascade="all, delete-orphan"
    )

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])

    def to_dict(self, include_pole=True):
        data = {
            "id": self.id,
            "pole_id": self.pole_id,
            "caller_name": self.caller_name,
            "caller_phone": self.caller_phone,
            "description": self.description,
            "remarks": self.remarks,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
        }
        if include_pole and self.pole:
            data["pole_number"] = self.pole.pole_number
            data["ward"] = self.pole.ward
            data["location"] = self.pole.location
        if self.work_record:
            data["assigned_electrician"] = (
                self.work_record.electrician.name if self.work_record.electrician else None
            )
        return data
