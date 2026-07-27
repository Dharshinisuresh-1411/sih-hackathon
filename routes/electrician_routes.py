import re
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from models import db
from models.electrician import Electrician

electrician_bp = Blueprint("electrician_bp", __name__, url_prefix="/api/electricians")
PHONE_RE = re.compile(r"^[6-9]\d{9}$")


@electrician_bp.route("", methods=["GET"])
def list_electricians():
    try:
        active_only = request.args.get("active_only") == "true"
        query = Electrician.query
        if active_only:
            query = query.filter_by(is_active=True)
        electricians = query.order_by(Electrician.name.asc()).all()
        return jsonify([e.to_dict() for e in electricians]), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@electrician_bp.route("", methods=["POST"])
def create_electrician():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    is_active = data.get("is_active", True)

    if not name or not phone:
        return jsonify({"error": "name and phone are required."}), 400
    if not PHONE_RE.match(phone):
        return jsonify({"error": "phone must be a valid 10-digit mobile number."}), 400

    try:
        electrician = Electrician(name=name, phone=phone, is_active=bool(is_active))
        db.session.add(electrician)
        db.session.commit()
        return jsonify(electrician.to_dict()), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@electrician_bp.route("/<int:electrician_id>/toggle", methods=["POST"])
def toggle_electrician(electrician_id):
    try:
        electrician = Electrician.query.get(electrician_id)
        if not electrician:
            return jsonify({"error": f"Electrician {electrician_id} does not exist."}), 404
        electrician.is_active = not electrician.is_active
        db.session.commit()
        return jsonify(electrician.to_dict()), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500
