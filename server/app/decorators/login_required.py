from functools import wraps
from flask import request, jsonify

import server.app.services.auth_service as auth_service
from server.extensions import db


def login_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    token = request.cookies.get("access_token")
    account = auth_service.verify_user(token)
    if not account:
      return jsonify({"message": "Unauthorized."}), 401
    account = db.session.merge(account)
    return f(account, *args, **kwargs)
  return decorated