from functools import wraps

from flask import jsonify

from server.app.decorators.login_required import login_required


def role_required(*roles):
  def decorator(f):
    @wraps(f)
    @login_required
    def decorated(user, *args, **kwargs):
      if user.__class__.__name__.lower() not in roles:
        return jsonify({"message": "Forbidden."}), 403
      return f(user, *args, **kwargs)
    return decorated
  return decorator