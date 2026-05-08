import os
from datetime import datetime

import click
from flask import Flask

from server.app.models.match_rule import MatchRuleSet  # noqa: F401 – needed for db.create_all()
from server.app.routes.sport_type_routes import sport_type_bp
from server.app.routes.team import team_bp
from server.app.routes.match_rule import match_rule_bp, match_rule_set_bp
from server.app.routes.matcher import matches_bp
from server.app.routes.match_routes import match_proposals_bp
from server.config import SECRET_KEY, config_data
from server.extensions import db, babel
from server.app.routes.auth_routes import auth_bp
from server.app.routes.availability_routes import availability_bp
from server.app.routes.clubs_routes import clubs_bp
from server.app.routes.dashboard_routes import dashboard_bp
from server.app.routes.health_routes import api
from server.app.routes.root_routes import root_bp
from server.app.routes.ladder_routes import ladder_bp
from server.app.routes.ladders_routes import ladders_bp
from server.app.routes.rule_set_routes import rule_set_bp
from server.app.routes.rating_function_routes import rating_function_bp
from server.app.routes.weather_routes import weather
from server.app.utils.db_loader import load_sql
from server.app.utils.seed_table import seed_table
from server.app.models.account import Account, AccountRole
from server.app.models.ladder import LadderRatingFunction
from server.app.models.match import MatchStatus
from server.app.models.venue_type import VenueType
from server.app.models.sport_type import SportType
from server.app.services.weekly_match_proposal_service import (
    generate_weekly_match_proposals,
    next_week_start,
)
from sqlalchemy import text

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql+psycopg://{config_data['db_username']}:{config_data['db_password']}"
        f"@{config_data['db_host']}:{config_data['db_port']}/{config_data['db_name']}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["BABEL_DEFAULT_LOCALE"] = "en"
    app.config["BABEL_SUPPORTED_LOCALES"] = ["en", "nl"]
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"

    db.init_app(app)

    def get_locale():
        from flask import request
        lang = request.args.get("lang")
        if lang in app.config["BABEL_SUPPORTED_LOCALES"]:
            return lang
        return app.config["BABEL_DEFAULT_LOCALE"]

    babel.init_app(app, locale_selector=get_locale)

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
    _register_cli_commands(app)
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
    app.register_blueprint(matches_bp)
    app.register_blueprint(clubs_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(sport_type_bp)
    app.register_blueprint(match_rule_bp)
    app.register_blueprint(match_rule_set_bp)
    app.register_blueprint(match_proposals_bp)
    app.register_blueprint(rule_set_bp)
    app.register_blueprint(rating_function_bp)
    app.register_blueprint(weather)


def _register_cli_commands(app: Flask):
    @app.cli.command("generate-weekly-match-proposals")
    @click.option(
        "--week-start",
        "week_start",
        default=None,
        help="Monday week start date in YYYY-MM-DD format. Defaults to next week.",
    )
    @click.option(
        "--proposer-email",
        "proposer_email",
        default=None,
        help="Account email to store as proposed_by_user_id. Defaults to WEEKLY_MATCH_PROPOSER_EMAIL or the first account.",
    )
    @click.option(
        "--duration-minutes",
        "duration_minutes",
        default=60,
        show_default=True,
        type=int,
        help="Required overlapping availability duration.",
    )
    @click.option(
        "--location",
        "location",
        default=None,
        help="Optional location stored on generated proposals.",
    )
    def generate_weekly_match_proposals_command(week_start, proposer_email, duration_minutes, location):
        """Generate next week's ladder match proposals from player availability."""
        # This command is intended for cron/systemd. It runs outside the web
        # request cycle, while the generator remains reusable by routes/tests.
        target_week_start = next_week_start()
        if week_start:
            try:
                target_week_start = datetime.strptime(week_start, "%Y-%m-%d").date()
            except ValueError as exc:
                raise click.ClickException("week-start must be YYYY-MM-DD.") from exc

        account = _resolve_weekly_proposal_account(proposer_email)
        if not account:
            raise click.ClickException(
                "No proposer account found. Seed users first or pass --proposer-email."
            )

        result = generate_weekly_match_proposals(
            proposed_by_user_id=account.id,
            week_start_date=target_week_start,
            managed_team_ids=None,
            duration_minutes=duration_minutes,
            location=location,
        )

        click.echo(
            "Weekly match proposals generated "
            f"for {result['week_start_date']}: "
            f"created={result['created_count']}, skipped={result['skipped_count']}"
        )


def _resolve_weekly_proposal_account(proposer_email: str | None):
    configured_email = proposer_email or os.getenv("WEEKLY_MATCH_PROPOSER_EMAIL")
    if configured_email:
        return Account.query.filter_by(email=configured_email).first()
    return Account.query.order_by(Account.id.asc()).first()


def init_db(app: Flask):
    """
    Protocol 1 — Schema initialisation.
    Creates all tables (via schema.sql + SQLAlchemy) and seeds
    static reference data (page texts, roles, rulesets, rating functions).
    Safe to run repeatedly — all operations are idempotent.
    """
    with app.app_context():
        load_sql([
            "server/sql/infrastructure.sql",
            "server/sql/account.sql",
            "server/sql/club_and_team.sql",
            "server/sql/match_rules.sql",
            "server/sql/schema.sql",
            "server/sql/match.sql",
            "server/sql/triggers.sql"
        ])
        db.create_all()


        _seed_reference_tables()

        print("[init_db] Database initialisation complete.")

def seed_db(app: Flask, verbose: bool = True):
    """
    Protocol 2 — Development / demo seed.
    Populates teams, managers, players, demo club and ladders.
    Runs only when explicitly requested (SEED_ON_STARTUP=1 or called directly).
    Safe to run repeatedly — all helpers use get-or-create logic.
    """
    from server.seeds.seed_teams_and_users__match_edition import seed_teams_and_users
    with app.app_context():
        print("[seed_db] Running seed_teams_and_users...")
        seed_teams_and_users(verbose=verbose)
        print("[seed_db] Seed complete.")



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
    seed_table(
        model=MatchStatus,
        seeds_file="server/seeds/match_status.json",
        unique_fields=["name"],
    )
    seed_table(
        model=VenueType,
        seeds_file="server/seeds/venue_type.json",
        unique_fields=["name"],
    )
    seed_table(
        model=SportType,
        seeds_file="server/seeds/sport_type.json",
        unique_fields=["name"],
    )
