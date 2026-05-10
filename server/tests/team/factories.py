"""
Shared test factories for team-related test modules.

"""

from server.extensions import db
from server.app.models.account import Account, AccountRole, Administrator
from server.app.models.team import Team, TeamManager, TeamManagerTeam
from server.app.models.player import Player, PlayerTeam
from server.app.models.ladder_team import LadderTeam


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _role(name: str) -> AccountRole:
    role = AccountRole.query.filter_by(name=name).first()
    if not role:
        role = AccountRole(name=name)
        db.session.add(role)
        db.session.flush()
    return role


# ---------------------------------------------------------------------------
# Public factories
# ---------------------------------------------------------------------------

def _make_account(*, email: str, role_name="team_manager") -> Account:
    r = _role(role_name)
    acc = Account(
        email=email,
        password_hash="hashed",
        first_name="First",
        last_name="Last",
        account_role_id=r.id,
        is_verified=True,
    )
    db.session.add(acc)
    db.session.flush()
    return acc


def _make_team(*, name: str, club_id=None) -> Team:
    t = Team(name=name, club_id=club_id)
    db.session.add(t)
    db.session.flush()
    return t


def _make_team_manager(account: Account) -> TeamManager:
    existing = TeamManager.query.get(account.id)
    if existing:
        return existing
    tm = TeamManager(id=account.id)
    db.session.add(tm)
    db.session.flush()
    return tm


def _make_assoc(tm: TeamManager, team: Team, *,
                can_rename=True, can_delete=True,
                can_edit_players=True, can_edit_managers=True) -> TeamManagerTeam:
    a = TeamManagerTeam(
        team_manager_id=tm.id,
        team_id=team.id,
        can_rename=can_rename,
        can_delete=can_delete,
        can_edit_players=can_edit_players,
        can_edit_managers=can_edit_managers,
    )
    db.session.add(a)
    db.session.flush()
    return a


def _make_sport_type(*, min_players=None, max_players=None, name):
    from server.app.models.sport_type import SportType
    st = SportType(
        name=name,
        minimum_number_of_players_on_a_team=min_players,
        maximum_number_of_players_per_team=max_players,
    )
    db.session.add(st)
    db.session.flush()
    return st


def _make_ladder(*, name):
    from server.app.models.ladder import Ladder
    from server.app.models.club import Club
    club = Club(name=f"Club for {name}")
    db.session.add(club)
    db.session.flush()
    ladder = Ladder(name=name, club_id=club.id)
    db.session.add(ladder)
    db.session.flush()
    return ladder


def _enroll(team, ladder):
    lt = LadderTeam(ladder_id=ladder.id, team_id=team.id)
    db.session.add(lt)
    db.session.flush()
    return lt


def _add_player_to_team(team: Team, email: str) -> Account:
    acc = _make_account(email=email)
    player = Player(id=acc.id)
    db.session.add(player)
    db.session.flush()
    db.session.add(PlayerTeam(player_id=player.id, team_id=team.id))
    db.session.flush()
    return acc


def _make_admin(email: str) -> Account:
    """Creates an Account + Administrator row and returns the account."""
    acc = _make_account(email=email, role_name="administrator")
    db.session.add(Administrator(id=acc.id, access_level=0))
    db.session.flush()
    return acc
