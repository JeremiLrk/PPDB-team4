from flask import jsonify

from server.app.models.account import Account
from server.app.models.account_role import AccountRole 
from server.app.models.player import Player
from server.app.models.account import TeamManager
from server.extensions import db


def _get_or_create_role(name: str) -> AccountRole:
    """Returns an AccountRole by name, creating it if it doesn't exist."""
    role = AccountRole.query.filter_by(name=name).first()
    if not role:
        role = AccountRole(name=name)
        db.session.add(role)
        db.session.flush()
    return role


"""Utility functions for promoting accounts to new roles."""
def promote_to_player(target: Account) -> None:
    """Promotes an account to Player if it is not already one."""
    if target.player:
        return None  # already exists

    player_role = _get_or_create_role("player")

    db.session.add(Player(id=target.id))
    target.account_role_id = player_role.id
    db.session.flush()

    # expire forces SQLAlchemy to reload all attributes (including relationships)
    # on next access, ensuring target.player reflects the newly inserted row.
    db.session.expire(target)


def promote_to_team_manager(target: Account) -> None:
    """Promotes an account to TeamManager if it is not already one."""
    if target.team_manager:
        return None  # already exists

    tm_role = _get_or_create_role("team_manager")

    new_tm = TeamManager(id=target.id)
    db.session.add(new_tm)
    target.account_role_id = tm_role.id
    db.session.flush()

    # expire forces SQLAlchemy to reload all attributes (including relationships)
    # on next access, ensuring target.team_manager reflects the newly inserted row.
    db.session.expire(target)

    if not target.team_manager:
        abort(500, description="TeamManager entity was not created.")

    return None