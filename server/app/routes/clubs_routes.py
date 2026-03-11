from flask import Blueprint, jsonify
from sqlalchemy.exc import SQLAlchemyError

from server.app.models.club import Club

clubs_bp = Blueprint("clubs", __name__, url_prefix="/api")

# Temporary fake club so the per-club flow can be tested without complete DB seed data.
FAKE_CLUB = {"id": 99999, "name": "Mock Racket Club"}


@clubs_bp.get("/clubs")
def list_clubs():
    clubs = []
    try:
        db_clubs = Club.query.order_by(Club.name.asc()).all()
        clubs = [{"id": club.id, "name": club.name} for club in db_clubs]
    except SQLAlchemyError:
        clubs = []

    clubs.append(FAKE_CLUB)
    return jsonify({"clubs": clubs}), 200


@clubs_bp.get("/clubs/<int:club_id>")
def get_club(club_id: int):
    if club_id == FAKE_CLUB["id"]:
        return jsonify({"club": FAKE_CLUB}), 200

    try:
        club = Club.query.filter_by(id=club_id).first()
    except SQLAlchemyError:
        return jsonify({"message": "Club data unavailable"}), 500

    if not club:
        return jsonify({"message": "Club not found"}), 404

    return jsonify({"club": {"id": club.id, "name": club.name}}), 200
