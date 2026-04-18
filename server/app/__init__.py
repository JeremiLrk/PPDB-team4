import os
from datetime import datetime

import click
from flask import Flask

from server.app.routes.sport_type_routes import sport_type_bp
from server.app.routes.team_routes import team_bp
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
from server.app.routes.match_routes import matches_bp
from server.app.routes.texts_routes import texts
from server.app.utils.db_loader import load_sql
from server.app.utils.seed_table import seed_table
from server.app.models.page_text import PageText
from server.seeds.seed_teams_and_users import seed_teams_and_users
from server.app.models.account_role import AccountRole
from server.app.models.account import Account
from server.app.models.ladder import MatchRuleSet, LadderRatingFunction, Ladder
from server.app.models.match import MatchStatus, VenueType
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
    _register_cli_commands(app)
    _init_db(app)

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
    app.register_blueprint(texts)
    app.register_blueprint(team_bp)
    app.register_blueprint(sport_type_bp)


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
        seed_table(
            model=MatchRuleSet,
            seeds_file="server/seeds/match_rule_set.json",
            unique_fields=["name"],
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
            model=LadderRatingFunction,
            seeds_file="server/seeds/ladder_rating_function.json",
            unique_fields=["name"],
        )
        seed_teams_and_users()
