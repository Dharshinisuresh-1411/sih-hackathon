from datetime import datetime
from . import db


class WorkRecord(db.Model):
    """One row per complaint, created at assignment time, updated at closure.
    Holds full accountability trail: who assigned, who closed, what was
    repaired/replaced."""

    __tablename__ = "work_records"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(
        db.Integer, db.ForeignKey("complaints.id"), nullable=False, unique=True, index=True
    )
    electrician_id = db.Column(db.Integer, db.ForeignKey("electricians.id"), nullable=False)

    assigned_by = db.Column(db.String(100), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    closed_by = db.Column(db.String(100), nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    repair_note = db.Column(db.Text, nullable=True)
    replaced_item = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "electrician_id": self.electrician_id,
            "electrician_name": self.electrician.name if self.electrician else None,
            "assigned_by": self.assigned_by,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "closed_by": self.closed_by,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "repair_note": self.repair_note,
            "replaced_item": self.replaced_item,
        }
