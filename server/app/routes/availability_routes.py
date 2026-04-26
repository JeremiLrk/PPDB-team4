from flask import Blueprint, jsonify, request

from server.app.services.auth_service import verify_user
from server.app.services.availability_service import (
    create_block_for_user,
    delete_block_for_user,
    has_overlap,
    list_blocks_for_user,
    parse_timestamp,
    parse_time_value,
    parse_weekday,
)

availability_bp = Blueprint("availability", __name__, url_prefix="/api/me/availability")

def _get_current_user():
    token = request.cookies.get("access_token")
    return verify_user(token)

@availability_bp.get("")
def get_my_availability():
    account = _get_current_user()
    if not account:
        return jsonify({"message": "Unauthorized."}), 401

    return jsonify({"availability": list_blocks_for_user(account.id)}), 200

@availability_bp.post("")
def create_my_availability_block():
    account = _get_current_user()
    if not account:
        return jsonify({"message": "Unauthorized."}), 401

    data = request.get_json() or {}
    weekday = parse_weekday(data.get("weekday"))
    start_time_value = parse_time_value(data.get("start_time"))
    end_time_value = parse_time_value(data.get("end_time"))

    if weekday is None or start_time_value is None or end_time_value is None:
        start_at = parse_timestamp(data.get("start_at"))
        end_at = parse_timestamp(data.get("end_at"))
        if start_at and end_at:
            weekday = start_at.weekday()
            start_time_value = start_at.time().replace(microsecond=0)
            end_time_value = end_at.time().replace(microsecond=0)

    if weekday is None or start_time_value is None or end_time_value is None:
        return jsonify({"message": "weekday, start_time, and end_time are required."}), 400

    if start_time_value >= end_time_value:
        return jsonify({"message": "start_time must be before end_time."}), 400

    if has_overlap(account.id, weekday, start_time_value, end_time_value):
        return jsonify({"message": "Availability overlaps with an existing weekly block."}), 409

    block = create_block_for_user(account.id, weekday, start_time_value, end_time_value)
    return jsonify({"block": block}), 201

@availability_bp.delete("/<int:block_id>")
def delete_my_availability_block(block_id):
    account = _get_current_user()
    if not account:
        return jsonify({"message": "Unauthorized."}), 401

    deleted = delete_block_for_user(account.id, block_id)
    if not deleted:
        return jsonify({"message": "Availability block not found."}), 404

    return jsonify({"message": "Availability block deleted."}), 200
