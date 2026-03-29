from flask import Flask

from server.app.routes.sport_type_routes import sport_type_bp
from server.app.routes.team_routes import team_bp
from server.config import SECRET_KEY, config_data
from server.extensions import db
from server.app.routes.auth_routes import auth_bp
from server.app.routes.clubs_routes import clubs_bp
from server.app.routes.dashboard_routes import dashboard_bp
from server.app.routes.health_routes import api
from server.app.routes.root_routes import root_bp
from server.app.routes.ladder_routes import ladder_bp
from server.app.routes.ladders_routes import ladders_bp
from server.app.routes.texts_routes import texts
from server.app.utils.db_loader import load_sql
from server.app.utils.seed_table import seed_table
from server.app.models.page_text import PageText
from server.seeds.seed_teams_and_users import seed_teams_and_users
from server.app.models.account_role import AccountRole
from sqlalchemy import text


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql+psycopg://{config_data['db_username']}:{config_data['db_password']}"
        f"@{config_data['db_host']}:{config_data['db_port']}/{config_data['db_name']}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = SECRET_KEY

    db.init_app(app)    

    with app.app_context():
        print("Dropping all tables including dependencies...")
        db.session.execute(text("DROP SCHEMA public CASCADE"))
        db.session.execute(text("CREATE SCHEMA public"))
        db.session.execute(text("GRANT ALL ON SCHEMA public TO public"))  # restore rights
        db.session.commit()
        print("Database schema reset complete.")

    _register_blueprints(app)
    _init_db(app)

    @app.get("/")
    def root():
        return {"message": "API running"}, 200

    return app


def _register_blueprints(app: Flask):
    app.register_blueprint(root_bp)
    app.register_blueprint(api)
    app.register_blueprint(auth_bp)
    app.register_blueprint(ladders_bp)
    app.register_blueprint(ladder_bp)
    app.register_blueprint(clubs_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(texts)
    app.register_blueprint(team_bp)
    app.register_blueprint(sport_type_bp)


def _init_db(app: Flask):
    with app.app_context():
        load_sql("server/sql/schema.sql")
        db.create_all()

        seed_table(
            model=PageText,
            seeds_file="server/seeds/page_text_base.json",
            unique_fields=["page", "key", "language"],
        )
        seed_table(
            model=PageText,
            seeds_file="server/seeds/page_text_home.json",
            unique_fields=["page", "key", "language"],
        )
        seed_table(
            model=PageText,
            seeds_file="server/seeds/page_text_authorization.json",
            unique_fields=["page", "key", "language"],
        )
        seed_table(
            model=PageText,
            seeds_file="server/seeds/page_text_ladder.json",
            unique_fields=["page", "key", "language"],
        )
        seed_table(
            model=PageText,
            seeds_file="server/seeds/page_text_score.json",
            unique_fields=["page", "key", "language"],
        )
        seed_table(
            model=PageText,
            seeds_file="server/seeds/page_text_dashboard.json",
            unique_fields=["page", "key", "language"],
        )
        seed_table(
            model=PageText,
            seeds_file="server/seeds/page_text_landing.json",
            unique_fields=["page", "key", "language"],
        )
        seed_table(
            model=PageText,
            seeds_file="server/seeds/page_text_club_home.json",
            unique_fields=["page", "key", "language"],
        )
        seed_table(
            model=AccountRole,
            seeds_file="server/seeds/account_role.json",
            unique_fields=[],
        )
        seed_teams_and_users()
