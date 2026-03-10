from flask import Flask
from server.config import config_data, SECRET_KEY
from server.app.models.user import db
from server.app.routes.auth_routes import auth_bp
from server.app.routes.clubs_routes import clubs_bp
from server.app.routes.dashboard_routes import dashboard_bp
from server.app.routes.health_routes import api
from server.app.routes.root_routes import root_bp
from server.app.utils.db_loader import load_sql

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg://{config_data['db_username']}:{config_data['db_password']}@{config_data['db_host']}:{config_data['db_port']}/{config_data['db_name']}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = SECRET_KEY

    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(root_bp)
    app.register_blueprint(api)
    app.register_blueprint(auth_bp)
    app.register_blueprint(clubs_bp)
    app.register_blueprint(dashboard_bp)


    # Load SQL and create tables
    with app.app_context():
        load_sql()

    @app.get("/")
    def root():
        return {"message": "API running"}, 200

    return app
