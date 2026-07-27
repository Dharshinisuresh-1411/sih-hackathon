from datetime import datetime
from . import db


class Pole(db.Model):
    """A physical street-light pole. This is the central entity of the
    system: complaints are anchored to a pole, not to a caller."""

    __tablename__ = "poles"

    STATUS_WORKING = "WORKING"
    STATUS_DARK = "DARK"
    STATUS_UNDER_REPAIR = "UNDER_REPAIR"
    STATUS_MAINTENANCE_REQUIRED = "MAINTENANCE_REQUIRED"

    VALID_STATUSES = [
        STATUS_WORKING,
        STATUS_DARK,
        STATUS_UNDER_REPAIR,
        STATUS_MAINTENANCE_REQUIRED,
    ]

    id = db.Column(db.Integer, primary_key=True)
    pole_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    ward = db.Column(db.String(50), nullable=False, index=True)
    location = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(30), nullable=False, default=STATUS_WORKING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    complaints = db.relationship(
        "Complaint", backref="pole", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "pole_number": self.pole_number,
            "ward": self.ward,
            "location": self.location,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
