from flask import Blueprint

root_bp = Blueprint("root", __name__)

@root_bp.get("/")
def root():
    """Endpoint to check if the API is running."""
    return {"message": "API running"}, 200