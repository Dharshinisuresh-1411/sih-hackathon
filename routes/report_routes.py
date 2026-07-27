from datetime import datetime, timedelta
from flask import Blueprint, jsonify, current_app
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from models import db
from models.pole import Pole
from models.complaint import Complaint
from models.electrician import Electrician

report_bp = Blueprint("report_bp", __name__, url_prefix="/api/reports")


@report_bp.route("/summary", methods=["GET"])
def summary():
    """Dashboard KPI numbers."""
    try:
        months = current_app.config["REPEAT_OFFENDER_MONTHS"]
        since = datetime.utcnow() - timedelta(days=30 * months)

        repeat_offender_poles = (
            db.session.query(Complaint.pole_id)
            .filter(Complaint.created_at >= since)
            .group_by(Complaint.pole_id)
            .having(func.count(Complaint.id) >= 2)
            .count()
        )

        data = {
            "total_poles": Pole.query.count(),
            "total_complaints": Complaint.query.count(),
            "open_complaints": Complaint.query.filter_by(status=Complaint.STATUS_OPEN).count(),
            "assigned_complaints": Complaint.query.filter_by(status=Complaint.STATUS_ASSIGNED).count(),
            "in_progress_complaints": Complaint.query.filter_by(status=Complaint.STATUS_IN_PROGRESS).count(),
            "closed_complaints": Complaint.query.filter_by(status=Complaint.STATUS_CLOSED).count(),
            "active_electricians": Electrician.query.filter_by(is_active=True).count(),
            "repeat_offender_poles": repeat_offender_poles,
            "repeat_offender_period_months": months,
        }
        return jsonify(data), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@report_bp.route("/open-by-ward", methods=["GET"])
def open_by_ward():
    try:
        rows = (
            db.session.query(Pole.ward, func.count(Complaint.id))
            .join(Complaint, Complaint.pole_id == Pole.id)
            .filter(Complaint.status != Complaint.STATUS_CLOSED)
            .group_by(Pole.ward)
            .order_by(Pole.ward.asc())
            .all()
        )
        return jsonify([{"ward": w, "open_complaints": c} for w, c in rows]), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@report_bp.route("/status-distribution", methods=["GET"])
def status_distribution():
    try:
        rows = (
            db.session.query(Complaint.status, func.count(Complaint.id))
            .group_by(Complaint.status)
            .all()
        )
        return jsonify({status: count for status, count in rows}), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@report_bp.route("/repeat-offenders", methods=["GET"])
def repeat_offenders():
    """Poles ranked by complaint count within the configured window.
    Pure SQL aggregation — nothing here is manually entered."""
    try:
        months = current_app.config["REPEAT_OFFENDER_MONTHS"]
        since = datetime.utcnow() - timedelta(days=30 * months)

        rows = (
            db.session.query(
                Pole.id,
                Pole.pole_number,
                Pole.ward,
                Pole.location,
                Pole.status,
                func.count(Complaint.id).label("total_complaints"),
                func.max(Complaint.created_at).label("last_complaint_date"),
            )
            .join(Complaint, Complaint.pole_id == Pole.id)
            .filter(Complaint.created_at >= since)
            .group_by(Pole.id)
            .order_by(func.count(Complaint.id).desc())
            .all()
        )

        result = []
        for rank, row in enumerate(rows, start=1):
            result.append({
                "rank": rank,
                "pole_id": row.id,
                "pole_number": row.pole_number,
                "ward": row.ward,
                "location": row.location,
                "pole_status": row.status,
                "total_complaints": row.total_complaints,
                "last_complaint_date": row.last_complaint_date.isoformat() if row.last_complaint_date else None,
                "high_frequency": row.total_complaints >= 4,
            })

        return jsonify({"ranking_period_months": months, "poles": result}), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500
