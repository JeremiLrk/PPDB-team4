from flask import Flask
from werkzeug.datastructures import ImmutableMultiDict

from server.app.models.account import Administrator, ClubOwner, TeamManager
from server.app.models.club import Club
from server.app.models.team import Team
from server.app.routes.team_routes import _can_edit_team, _parse_pagination


def test_parse_pagination_valid_values():
    args = ImmutableMultiDict([("from", "5"), ("to", "15"), ("sort", "name")])
    offset, limit, sort_col, err = _parse_pagination(args)

    assert err is None
    assert offset == 5
    assert limit == 10
    assert "team.name" in str(sort_col)


def test_parse_pagination_invalid_integer_returns_422():
    app = Flask(__name__)
    with app.app_context():
        args = ImmutableMultiDict([("from", "abc"), ("to", "10"), ("sort", "id")])
        offset, limit, sort_col, err = _parse_pagination(args)

    assert offset is None
    assert limit is None
    assert sort_col is None
    response, status = err
    assert status == 422
    assert "must be integers" in response.get_json()["message"]


def test_parse_pagination_invalid_sort_returns_422():
    app = Flask(__name__)
    with app.app_context():
        args = ImmutableMultiDict([("from", "0"), ("to", "20"), ("sort", "rating")])
        offset, limit, sort_col, err = _parse_pagination(args)

    assert offset is None
    assert limit is None
    assert sort_col is None
    response, status = err
    assert status == 422
    assert "must be 'id' or 'name'" in response.get_json()["message"]


def test_can_edit_team_for_administrator():
    admin = Administrator(access_level=1)
    team = Team(name="Any Team", club_id=10)

    assert _can_edit_team(admin, team) is True


def test_can_edit_team_for_club_owner_when_owns_club():
    club = Club(name="NetRank Club")
    team = Team(name="Club Team", club_id=1)
    team.club = club

    owner = ClubOwner()
    owner.clubs = [club]
    owner.teams = []

    assert _can_edit_team(owner, team) is True


def test_can_edit_team_for_team_manager_only_without_club():
    managed_team = Team(name="Managed Open Team", club_id=None)
    team_with_club = Team(name="Managed Club Team", club_id=33)

    manager = TeamManager()
    manager.teams = [managed_team, team_with_club]

    assert _can_edit_team(manager, managed_team) is True
    assert _can_edit_team(manager, team_with_club) is False


def test_can_edit_team_for_unknown_role_returns_false():
    team = Team(name="No Access Team", club_id=None)
    assert _can_edit_team(object(), team) is False
