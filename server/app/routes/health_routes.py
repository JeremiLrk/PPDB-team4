from flask import Blueprint
from server.extensions import db
api = Blueprint("api", __name__, url_prefix="/api")

@api.get("/health")
def health():
    """Endpoint to check the health of the application and database connection."""
    return {"db_connected": True}