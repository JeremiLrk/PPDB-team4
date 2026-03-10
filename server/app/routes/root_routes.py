from flask import Blueprint

root_bp = Blueprint("root", __name__)

@root_bp.get("/")
def root():
    return {"message": "API running"}