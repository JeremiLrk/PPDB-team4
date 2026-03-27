from datetime import datetime

from flask import Blueprint, jsonify, request

from server.app.services.auth_service import verify_user
from server.app.services.availability_service import (
    create_block_for_user,
    delete_block_for_user,
    has_overlap,
    list_blocks_for_user,
    parse_timestamp,
)

availability_bp = Blueprint("availability", __name__, url_prefix="/api/me/availability")

def _get_current_user():
    token = request.cookies.get("access_token")
    return verify_user(token)

@availability_bp.get("")
def get_my_availability():
    user = _get_current_user()
    if not user:
        return jsonify({"message": "Unauthorized."}), 401

    return jsonify({"availability": list_blocks_for_user(user.id)}), 200

@availability_bp.post("")
def create_my_availability_block():
    user = _get_current_user()
    if not user:
        return jsonify({"message": "Unauthorized."}), 401

    data = request.get_json() or {}
    start_at = parse_timestamp(data.get("start_at"))
    end_at = parse_timestamp(data.get("end_at"))

    if not start_at or not end_at:
        return jsonify({"message": ("Invalid timestamp format.")}), 400

    if start_at >= end_at:
        return jsonify({"message": "start_at must be before end_at."}), 400

    if start_at <= datetime.utcnow():
        return jsonify({"message": "start_at must be in the future."}), 400

    if has_overlap(user.id, start_at, end_at):
        return jsonify({"message": "Availability block overlaps with an existing block."}), 409

    block = create_block_for_user(user.id, start_at, end_at)
    return jsonify({"block": block}), 201

@availability_bp.delete("/<int:block_id>")
def delete_my_availability_block(block_id):
    user = _get_current_user()
    if not user:
        return jsonify({"message": "Unauthorized."}), 401

    deleted = delete_block_for_user(user.id, block_id)
    if not deleted:
        return jsonify({"message": "Availability block not found."}), 404

    return jsonify({"message": "Availability block deleted."}), 200
