from flask import Flask
from server.extensions import db
from server.config import config_data, SECRET_KEY

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg://{config_data['db_username']}:{config_data['db_password']}@{config_data['db_host']}:{config_data['db_port']}/{config_data['db_name']}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = SECRET_KEY

    db.init_app(app)

    _register_blueprints(app)
    _init_db(app)

    return app

def _register_blueprints(app: Flask):
    from server.app.routes.texts_routes import texts
    from server.app.routes.auth_routes import auth_bp
    from server.app.routes.health_routes import api
    from server.app.routes.root_routes import root_bp

    app.register_blueprint(root_bp)
    app.register_blueprint(api)
    app.register_blueprint(auth_bp)
    app.register_blueprint(texts)


def _init_db(app: Flask):
    from server.app.utils.db_loader import load_sql
    from server.app.utils.seed_table import seed_table
    from server.app.models.PageText import PageText

    with app.app_context():

        # --- reset schema ---
        sql_file_path = "server/sql/schema.sql"
        load_sql(sql_file_path)
        db.create_all()

        # --- seed data ---
        seed_table(
            model=PageText,
            seeds_file="server/seeds/page_text.json",
            unique_fields=["page", "key", "language"]
        )

        seed_table(
            model=PageText,
            seeds_file="server/seeds/page_text_authorization.json",
            unique_fields=["page", "key", "language"]
        )
