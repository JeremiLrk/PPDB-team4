from flask import jsonify

from server.app.models.account import Account
from server.app.models.account_role import AccountRole 
from server.app.models.player import Player
from server.app.models.account import TeamManager
from server.extensions import db


def promote_to_player(target: Account):
  """Promotes an account to Player if it is not already one."""
  if target.player:
    return None  # already exists

  player_role = AccountRole.query.filter_by(name="player").first()
  if not player_role:
    return jsonify({"message": "Role 'player' not found in DB."}), 500

  db.session.add(Player(id=target.id))
  target.account_role_id = player_role.id
  db.session.flush()
  db.session.refresh(target)
  return None

def promote_to_team_manager(target: Account):
  """Promotes an account to TeamManager if it is not already one."""
  if target.team_manager:
    return None  # already exists

  tm_role = AccountRole.query.filter_by(name="team_manager").first()
  if not tm_role:
    return jsonify({"message": "Role 'team_manager' not found in DB."}), 500

  new_tm = TeamManager(id=target.id)
  db.session.add(new_tm)
  target.account_role_id = tm_role.id
  db.session.flush()
  db.session.refresh(target)
  return None

