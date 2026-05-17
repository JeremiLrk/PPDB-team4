from functools import wraps
from flask import request, jsonify

import server.app.services.auth_service as auth_service
from server.extensions import db


def login_required(f):
  """
    Checks for a valid login token in the request cookies and verifies the associated user account.

    Returns:
        the account found in the database

    Postconditions:
        - The request token is valid and corresponds to an existing user account.
    """
  @wraps(f)
  def decorated(*args, **kwargs):
    token = request.cookies.get("access_token")
    account = auth_service.verify_user(token)
    if not account:
      return jsonify({"message": "Unauthorized."}), 401
    account = db.session.merge(account)
    return f(account, *args, **kwargs)
  return decorated