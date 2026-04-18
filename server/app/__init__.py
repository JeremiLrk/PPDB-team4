import os


from flask import Flask

from server.app.errors import register_error_handlers
from server.app.models.match_rule import MatchRuleSet
from server.app.routes.sport_type_routes import sport_type_bp
from server.app.routes.team import team_bp
from server.app.routes.match_rule import match_rule_bp, match_rule_set_bp
from server.config import SECRET_KEY, config_data
from server.extensions import db
from server.app.routes.auth_routes import auth_bp
from server.app.routes.availability_routes import availability_bp
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
from server.app.models.account import AccountRole
from server.app.models.ladder import LadderRatingFunction, Ladder
from sqlalchemy import text

def create_app():
    app = Flask(__name__)
    register_error_handlers(app)

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql+psycopg://{config_data['db_username']}:{config_data['db_password']}"
        f"@{config_data['db_host']}:{config_data['db_port']}/{config_data['db_name']}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = SECRET_KEY

    db.init_app(app)    

    should_reset_db = os.getenv("RESET_DB_ON_STARTUP", "").lower() in {"1", "true", "yes"}
    if should_reset_db:
        with app.app_context():
            print("Dropping all tables including dependencies...")
            db.session.execute(text("DROP SCHEMA public CASCADE"))
            db.session.execute(text("CREATE SCHEMA public"))
            db.session.execute(text("GRANT ALL ON SCHEMA public TO public"))  # restore rights
            db.session.commit()
            print("Database schema reset complete.")

    _register_blueprints(app)
    init_db(app)

    should_seed = os.getenv("SEED_ON_STARTUP", "").lower() in {"1", "true", "yes"}
    if should_seed:
        seed_verbose = os.getenv("SEED_VERBOSE", "1").lower() not in {"0", "false", "no"}
        seed_db(app, verbose=seed_verbose)


    @app.get("/")
    def root():
        return {"message": "API running"}, 200

    return app


def _register_blueprints(app: Flask):
    app.register_blueprint(root_bp)
    app.register_blueprint(api)
    app.register_blueprint(auth_bp)
    app.register_blueprint(availability_bp)
    app.register_blueprint(ladders_bp)
    app.register_blueprint(ladder_bp)
    app.register_blueprint(clubs_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(texts)
    app.register_blueprint(team_bp)
    app.register_blueprint(sport_type_bp)
    app.register_blueprint(match_rule_bp)
    app.register_blueprint(match_rule_set_bp)


def init_db(app: Flask):
    """
    Protocol 1 — Schema initialisation.
    Creates all tables (via schema.sql + SQLAlchemy) and seeds
    static reference data (page texts, roles, rulesets, rating functions).
    Safe to run repeatedly — all operations are idempotent.
    """
    with app.app_context():
        load_sql("server/sql/schema.sql")
        db.create_all()

        _seed_page_texts()
        _seed_reference_tables()

        print("[init_db] Database initialisation complete.")

def seed_db(app: Flask, verbose: bool = True):
    """
    Protocol 2 — Development / demo seed.
    Populates teams, managers, players, demo club and ladders.
    Runs only when explicitly requested (SEED_ON_STARTUP=1 or called directly).
    Safe to run repeatedly — all helpers use get-or-create logic.
    """
    from server.seeds.seed_teams_and_users import seed_teams_and_users
    with app.app_context():
        print("[seed_db] Running seed_teams_and_users...")
        seed_teams_and_users(verbose=verbose)
        print("[seed_db] Seed complete.")


def _seed_page_texts():
    page_text_files = [
        "server/seeds/page_text_base.json",
        "server/seeds/page_text_home.json",
        "server/seeds/page_text_authorization.json",
        "server/seeds/page_text_ladder.json",
        "server/seeds/page_text_score.json",
        "server/seeds/page_text_dashboard.json",
        "server/seeds/page_text_landing.json",
        "server/seeds/page_text_club_home.json",
    ]
    for path in page_text_files:
        seed_table(
            model=PageText,
            seeds_file=path,
            unique_fields=["page", "key", "language"],
        )

def _seed_reference_tables():
    seed_table(
        model=AccountRole,
        seeds_file="server/seeds/account_role.json",
        unique_fields=["name"],
    )
    seed_table(
        model=MatchRuleSet,
        seeds_file="server/seeds/match_rule_set.json",
        unique_fields=[],
    )
    seed_table(
        model=LadderRatingFunction,
        seeds_file="server/seeds/ladder_rating_function.json",
        unique_fields=[],
    )