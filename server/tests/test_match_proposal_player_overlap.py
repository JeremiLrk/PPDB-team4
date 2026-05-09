from datetime import date, datetime, timedelta, timezone

from server.app.models.account import Account, AccountRole, Administrator
from server.app.models.availability_block import AvailabilityBlock
from server.app.models.club import Club
from server.app.models.ladder import Ladder, LadderRatingFunction
from server.app.models.ladder_team import LadderTeam
from server.app.models.match_rule import MatchRuleSet
from server.app.models.player import Player, PlayerTeam
from server.app.models.sport_type import SportType
from server.app.models.team import Team
from server.app.services.weekly_match_proposal_service import generate_weekly_match_proposals
from server.extensions import db
from server.tests._authed_client import _authed_client


def _get_role(role_name: str) -> AccountRole:
    role = AccountRole.query.filter_by(name=role_name).first()
    assert role is not None
    return role


def _make_account(email: str, *, role_name: str = "user", first_name: str = "Test", last_name: str = "User") -> Account:
    account = Account(
        email=email,
        password_hash="hashed",
        first_name=first_name,
        last_name=last_name,
        account_role_id=_get_role(role_name).id,
        is_verified=True,
    )
    db.session.add(account)
    db.session.flush()
    return account


def _make_player(account: Account) -> Player:
    player = db.session.get(Player, account.id)
    if player is not None:
        return player

    player = Player(id=account.id)
    db.session.add(player)
    db.session.flush()
    return player


def _make_admin_account(email: str) -> Account:
    account = _make_account(email, role_name="user", first_name="Admin", last_name="User")
    db.session.add(Administrator(id=account.id, access_level=1))
    db.session.flush()
    return account


def _make_team(name: str, *, sport_type_id: int, club_id: int | None = None) -> Team:
    team = Team(name=name, sport_type_id=sport_type_id, club_id=club_id)
    db.session.add(team)
    db.session.flush()
    return team


def _add_player_to_team(account: Account, team: Team) -> None:
    player = _make_player(account)
    if PlayerTeam.query.filter_by(player_id=player.id, team_id=team.id).first():
        return
    db.session.add(PlayerTeam(player_id=player.id, team_id=team.id))
    db.session.flush()


def _add_availability(account: Account, start_at: datetime, duration_hours: int = 2) -> None:
    end_at = start_at + timedelta(hours=duration_hours)
    db.session.add(
        AvailabilityBlock(
            user_id=account.id,
            weekday=start_at.weekday(),
            start_time=start_at.time(),
            end_time=end_at.time(),
            start_at=start_at,
            end_at=end_at,
        )
    )
    db.session.flush()


def _make_ladder(club: Club, sport_type: SportType) -> Ladder:
    rating_function = LadderRatingFunction.query.order_by(LadderRatingFunction.id.asc()).first()
    ruleset = MatchRuleSet.query.order_by(MatchRuleSet.id.asc()).first()
    assert rating_function is not None
    ladder = Ladder(
        club_id=club.id,
        name="Overlap Ladder",
        description="Test ladder",
        sport_type_id=sport_type.id,
        ruleset_id=ruleset.id if ruleset else None,
        ladder_rating_function_id=rating_function.id,
    )
    db.session.add(ladder)
    db.session.flush()
    return ladder


def _make_club(name: str, sport_type: SportType) -> Club:
    club = Club(name=name, sport_type_id=sport_type.id, city="Test City")
    db.session.add(club)
    db.session.flush()
    return club


def test_weekly_generator_skips_shared_player_pair(app):
    with app.app_context():
        tennis = SportType.query.filter_by(name="Tennis").first()
        assert tennis is not None

        club = _make_club("Overlap Club", tennis)
        team1 = _make_team("Overlap A", sport_type_id=tennis.id, club_id=club.id)
        team2 = _make_team("Overlap B", sport_type_id=tennis.id, club_id=club.id)
        ladder = _make_ladder(club, tennis)
        db.session.add_all(
            [
                LadderTeam(ladder_id=ladder.id, team_id=team1.id, rank=1, rating=1200, matches_played=0),
                LadderTeam(ladder_id=ladder.id, team_id=team2.id, rank=2, rating=1180, matches_played=0),
            ]
        )

        shared = _make_account("shared@example.com")
        _add_player_to_team(shared, team1)
        _add_player_to_team(shared, team2)
        week_start = date(2026, 5, 11)
        _add_availability(shared, datetime(2026, 5, 12, 18, 0))
        db.session.commit()

        result = generate_weekly_match_proposals(
            proposed_by_user_id=shared.id,
            week_start_date=week_start,
            ladder_id=ladder.id,
            managed_team_ids=None,
            duration_minutes=60,
            location="Overlap Court",
        )

        assert result["created_count"] == 0
        assert result["skipped_count"] == 1
        assert result["skipped"][0]["reason"] == "shared_players"


def test_match_proposal_route_rejects_shared_player_pair(app, client, monkeypatch):
    with app.app_context():
        tennis = SportType.query.filter_by(name="Tennis").first()
        assert tennis is not None

        club = _make_club("Route Overlap Club", tennis)
        team1 = _make_team("Route Overlap A", sport_type_id=tennis.id, club_id=club.id)
        team2 = _make_team("Route Overlap B", sport_type_id=tennis.id, club_id=club.id)

        shared = _make_account("route-shared@example.com")
        _add_player_to_team(shared, team1)
        _add_player_to_team(shared, team2)

        admin = _make_admin_account("route-admin@example.com")
        db.session.commit()
        team1_id = team1.id
        team2_id = team2.id
        sport_type_id = tennis.id
        admin_id = admin.id

    with app.app_context():
        admin = db.session.get(Account, admin_id)
        _authed_client(client, monkeypatch, admin)

    payload = {
        "team1_id": team1_id,
        "team2_id": team2_id,
        "sport_type_id": sport_type_id,
        "week_start_date": "2026-05-11",
        "proposed_start_at": "2026-05-12T18:00:00Z",
        "proposed_end_at": "2026-05-12T19:00:00Z",
    }
    resp = client.post("/api/matches/proposals", json=payload)
    assert resp.status_code == 422
    assert "cannot share players" in resp.get_json()["message"].lower()
