from functools import wraps
from flask import request, jsonify

from server.app.services.auth_service import verify_user


def login_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    token = request.cookies.get("access_token")
    account = verify_user(token)
    if not account:
      return jsonify({"message": "Unauthorized."}), 401
    return f(account, *args, **kwargs)
  return decorated