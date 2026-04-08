from flask import abort
from server.app.models.account import Account, AccountRole
from server.app.models.player import Player
from server.app.models.team import TeamManager
from server.extensions import db


def promote_to_player(target: Account) -> None:
    """Promotes an account to Player if it is not already one."""
    if target.player:
        return None  # already exists

    player_role = AccountRole.query.filter_by(name="player").first()
    if not player_role:
        abort(500, description="Role 'player' not found in DB.")

    db.session.add(Player(id=target.id))
    target.account_role_id = player_role.id
    db.session.flush()
    db.session.refresh(target)

    if not target.player:
        abort(500, description="Player entity was not created.")
    return None


def promote_to_team_manager(target: Account) -> None:
    """Promotes an account to TeamManager if it is not already one."""
    if target.team_manager:
        return None  # already exists

    tm_role = AccountRole.query.filter_by(name="team_manager").first()
    if not tm_role:
        abort(500, description="Role 'team_manager' not found in DB.")

    new_tm = TeamManager(id=target.id)
    db.session.add(new_tm)
    target.account_role_id = tm_role.id
    db.session.flush()
    db.session.refresh(target)

    if not target.team_manager:
        abort(500, description="TeamManager entity was not created.")

    return None

