import re
from datetime import datetime
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from models import db
from models.pole import Pole
from models.complaint import Complaint
from models.electrician import Electrician
from models.work_record import WorkRecord

complaint_bp = Blueprint("complaint_bp", __name__, url_prefix="/api/complaints")

PHONE_RE = re.compile(r"^[6-9]\d{9}$")  # Indian 10-digit mobile format


def _sync_pole_status(complaint):
    pole = complaint.pole
    if not pole:
        return

    if complaint.status == Complaint.STATUS_CLOSED:
        other_active = (
            Complaint.query.filter(
                Complaint.pole_id == pole.id,
                Complaint.id != complaint.id,
                Complaint.status != Complaint.STATUS_CLOSED,
            ).first()
        )
        pole.status = Pole.STATUS_WORKING if not other_active else Pole.STATUS_DARK
    elif complaint.status in {Complaint.STATUS_ASSIGNED, Complaint.STATUS_IN_PROGRESS}:
        pole.status = Pole.STATUS_UNDER_REPAIR
    else:
        pole.status = Pole.STATUS_DARK


@complaint_bp.route("", methods=["GET"])
def list_complaints():
    try:
        status = request.args.get("status")
        ward = request.args.get("ward")
        pole_number = request.args.get("pole_number")
        keyword = (request.args.get("q") or "").strip()

        query = Complaint.query.join(Pole)
        if status:
            query = query.filter(Complaint.status == status.upper())
        if ward:
            query = query.filter(Pole.ward == ward)
        if pole_number:
            query = query.filter(Pole.pole_number == pole_number.strip().upper())
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                db.or_(
                    Complaint.description.ilike(like),
                    Complaint.caller_name.ilike(like),
                    Complaint.caller_phone.ilike(like),
                    Complaint.remarks.ilike(like),
                    Pole.pole_number.ilike(like),
                    Pole.ward.ilike(like),
                    Pole.location.ilike(like),
                )
            )

        complaints = query.order_by(Complaint.created_at.desc()).all()
        return jsonify([c.to_dict() for c in complaints]), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@complaint_bp.route("/open", methods=["GET"])
def open_complaints():
    """Open (non-closed) complaints, grouped by ward — answers
    'what needs to be done today'."""
    try:
        complaints = (
            Complaint.query.join(Pole)
            .filter(Complaint.status != Complaint.STATUS_CLOSED)
            .order_by(Pole.ward.asc(), Complaint.created_at.asc())
            .all()
        )
        grouped = {}
        for c in complaints:
            grouped.setdefault(c.pole.ward, []).append(c.to_dict())
        return jsonify(grouped), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@complaint_bp.route("/<int:complaint_id>", methods=["GET"])
def get_complaint(complaint_id):
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({"error": f"Complaint {complaint_id} does not exist."}), 404
        return jsonify(complaint.to_dict()), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@complaint_bp.route("", methods=["POST"])
def create_complaint():
    """Register a new complaint. CRITICAL RULE: pole must exist. If the pole
    already has an OPEN (non-closed) complaint, we do NOT silently create a
    duplicate — we return the existing complaint with a 200/"duplicate" flag
    so the clerk can see it instead of dispatching an electrician twice.

    Design decision (see README): rather than blocking the second caller
    entirely, we surface the existing active complaint. This preserves the
    fact that another person called (useful for urgency/priority signal)
    while making it obvious to staff that no new work order is needed.
    """
    data = request.get_json(silent=True) or {}
    pole_number = (data.get("pole_number") or "").strip().upper()
    caller_name = (data.get("caller_name") or "").strip()
    caller_phone = (data.get("caller_phone") or "").strip()
    description = (data.get("description") or "").strip()
    remarks = (data.get("remarks") or "").strip()

    if not pole_number or not caller_name or not caller_phone or not description:
        return jsonify({
            "error": "pole_number, caller_name, caller_phone and description are required."
        }), 400

    if not PHONE_RE.match(caller_phone):
        return jsonify({"error": "caller_phone must be a valid 10-digit mobile number."}), 400

    try:
        pole = Pole.query.filter_by(pole_number=pole_number).first()
        if not pole:
            return jsonify({
                "error": f"Pole '{pole_number}' does not exist. Complaint rejected."
            }), 404

        existing_open = (
            Complaint.query.filter(
                Complaint.pole_id == pole.id, Complaint.status != Complaint.STATUS_CLOSED
            )
            .order_by(Complaint.created_at.desc())
            .first()
        )

        if existing_open:
            return jsonify({
                "duplicate": True,
                "message": (
                    f"Pole {pole.pole_number} already has an active complaint "
                    f"(#{existing_open.id}, status {existing_open.status}). "
                    "No new work order created — repeated call logged for reference."
                ),
                "existing_complaint": existing_open.to_dict(),
            }), 200

        complaint = Complaint(
            pole_id=pole.id,
            caller_name=caller_name,
            caller_phone=caller_phone,
            description=description,
            remarks=remarks or None,
            status=Complaint.STATUS_OPEN,
        )
        db.session.add(complaint)
        _sync_pole_status(complaint)
        db.session.commit()
        return jsonify({"duplicate": False, "complaint": complaint.to_dict()}), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@complaint_bp.route("/<int:complaint_id>/assign", methods=["POST"])
def assign_complaint(complaint_id):
    data = request.get_json(silent=True) or {}
    electrician_id = data.get("electrician_id")

    if not electrician_id:
        return jsonify({"error": "electrician_id is required."}), 400

    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({"error": f"Complaint {complaint_id} does not exist."}), 404

        electrician = Electrician.query.get(electrician_id)
        if not electrician:
            return jsonify({"error": f"Electrician {electrician_id} does not exist."}), 404

        # FAILURE CASE 2 — server-side enforced, never trust the frontend.
        if not electrician.is_active:
            return jsonify({
                "error": "Cannot assign complaint. Selected electrician is inactive."
            }), 400

        if not complaint.can_transition_to(Complaint.STATUS_ASSIGNED):
            return jsonify({
                "error": f"Complaint is '{complaint.status}' and cannot be assigned."
            }), 409

        # Single reliable transaction: create/replace work record AND flip status.
        work_record = complaint.work_record
        if work_record is None:
            work_record = WorkRecord(complaint_id=complaint.id)
            db.session.add(work_record)

        work_record.electrician_id = electrician.id
        work_record.assigned_by = ""
        work_record.assigned_at = datetime.utcnow()

        complaint.status = Complaint.STATUS_ASSIGNED
        complaint.version += 1
        complaint.updated_at = datetime.utcnow()
        _sync_pole_status(complaint)

        db.session.commit()
        return jsonify(complaint.to_dict()), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@complaint_bp.route("/<int:complaint_id>/start", methods=["POST"])
def start_complaint(complaint_id):
    """ASSIGNED -> IN_PROGRESS, e.g. electrician has arrived on site."""
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({"error": f"Complaint {complaint_id} does not exist."}), 404
        if not complaint.can_transition_to(Complaint.STATUS_IN_PROGRESS):
            return jsonify({
                "error": f"Complaint is '{complaint.status}'; cannot move to IN_PROGRESS."
            }), 409
        complaint.status = Complaint.STATUS_IN_PROGRESS
        complaint.version += 1
        complaint.updated_at = datetime.utcnow()
        _sync_pole_status(complaint)
        db.session.commit()
        return jsonify(complaint.to_dict()), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@complaint_bp.route("/<int:complaint_id>/close", methods=["POST"])
def close_complaint(complaint_id):
    """Close a complaint, recording repair details.

    FAILURE CASE 1 — concurrent closure: the client must send back the
    `version` it last saw (optimistic locking). We perform the status flip
    as a single UPDATE ... WHERE id=:id AND version=:version. If zero rows
    are affected, someone else already closed it first -> 409 Conflict.
    """
    data = request.get_json(silent=True) or {}
    closed_by = (data.get("closed_by") or "").strip()
    repair_note = (data.get("repair_note") or "").strip()
    replaced_item = (data.get("replaced_item") or "").strip()
    client_version = data.get("version")

    if not closed_by or not repair_note:
        return jsonify({"error": "closed_by and repair_note are required."}), 400
    if client_version is None:
        return jsonify({"error": "version is required to safely close the complaint."}), 400

    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({"error": f"Complaint {complaint_id} does not exist."}), 404

        if complaint.status == Complaint.STATUS_CLOSED:
            return jsonify({
                "error": "Complaint has already been closed by another user."
            }), 409

        if not complaint.can_transition_to(Complaint.STATUS_CLOSED):
            return jsonify({
                "error": f"Complaint is '{complaint.status}' and cannot be closed directly. "
                         "It must be ASSIGNED or IN_PROGRESS."
            }), 409

        # Atomic conditional update — the core of the optimistic lock.
        result = db.session.execute(
            db.update(Complaint)
            .where(Complaint.id == complaint_id, Complaint.version == int(client_version))
            .values(status=Complaint.STATUS_CLOSED, version=Complaint.version + 1,
                    updated_at=datetime.utcnow())
        )

        if result.rowcount == 0:
            db.session.rollback()
            return jsonify({
                "error": "Complaint has already been closed by another user."
            }), 409

        work_record = complaint.work_record
        if work_record is None:
            # Complaint closed without ever being formally assigned — still
            # record who closed it and what was done for accountability.
            work_record = WorkRecord(
                complaint_id=complaint.id,
                electrician_id=Electrician.query.first().id if Electrician.query.first() else None,
                assigned_by=closed_by,
            )
            db.session.add(work_record)

        work_record.closed_by = closed_by
        work_record.closed_at = datetime.utcnow()
        work_record.repair_note = repair_note
        work_record.replaced_item = replaced_item

        complaint.status = Complaint.STATUS_CLOSED
        complaint.version += 1
        complaint.updated_at = datetime.utcnow()
        _sync_pole_status(complaint)

        db.session.commit()
        db.session.refresh(complaint)
        return jsonify({"message": "Complaint closed successfully.",
                         "complaint": complaint.to_dict()}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500
