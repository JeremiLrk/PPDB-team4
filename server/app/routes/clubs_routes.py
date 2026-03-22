from flask import Blueprint, jsonify

from server.app.models.club import Club

clubs_bp = Blueprint("clubs", __name__, url_prefix="/api")

@clubs_bp.get("/clubs")
def list_clubs():
    db_clubs = Club.query.order_by(Club.name.asc()).all()
    clubs = [{"id": club.id, "name": club.name} for club in db_clubs]
    return jsonify({"clubs": clubs}), 200


@clubs_bp.get("/clubs/<int:club_id>")
def get_club(club_id: int):
    club = Club.query.filter_by(id=club_id).first()
    if not club:
        return jsonify({"message": "Club not found"}), 404

    return jsonify({"club": {"id": club.id, "name": club.name}}), 200
