import re
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models import db
from models.pole import Pole

pole_bp = Blueprint("pole_bp", __name__, url_prefix="/api/poles")

POLE_NUMBER_RE = re.compile(r"^[A-Za-z0-9\-]{2,20}$")


@pole_bp.route("", methods=["GET"])
def list_poles():
    try:
        ward = request.args.get("ward")
        query = Pole.query
        if ward:
            query = query.filter_by(ward=ward)
        poles = query.order_by(Pole.pole_number.asc()).all()
        return jsonify([p.to_dict() for p in poles]), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@pole_bp.route("/<pole_number>", methods=["GET"])
def get_pole(pole_number):
    try:
        pole = Pole.query.filter_by(pole_number=pole_number.strip().upper()).first()
        if not pole:
            return jsonify({"error": f"Pole '{pole_number}' does not exist."}), 404
        return jsonify(pole.to_dict()), 200
    except SQLAlchemyError:
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500


@pole_bp.route("", methods=["POST"])
def create_pole():
    data = request.get_json(silent=True) or {}
    pole_number = (data.get("pole_number") or "").strip().upper()
    ward = (data.get("ward") or "").strip()
    location = (data.get("location") or "").strip()
    status = (data.get("status") or Pole.STATUS_WORKING).strip().upper()

    if not pole_number or not ward or not location:
        return jsonify({"error": "pole_number, ward and location are required."}), 400
    if not POLE_NUMBER_RE.match(pole_number):
        return jsonify({"error": "pole_number format is invalid."}), 400
    if status not in Pole.VALID_STATUSES:
        return jsonify({"error": f"status must be one of {Pole.VALID_STATUSES}."}), 400

    try:
        if Pole.query.filter_by(pole_number=pole_number).first():
            return jsonify({"error": f"Pole '{pole_number}' already exists."}), 409

        pole = Pole(pole_number=pole_number, ward=ward, location=location, status=status)
        db.session.add(pole)
        db.session.commit()
        return jsonify(pole.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": f"Pole '{pole_number}' already exists."}), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to process your request because the database "
                                  "is temporarily unavailable. Please try again."}), 500
