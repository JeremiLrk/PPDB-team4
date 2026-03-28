from flask import Blueprint, request, jsonify

from server.app.utils.promote import promote_to_team_manager, promote_to_player
from server.extensions import db
from server.app.models.account import Account, TeamManager, ClubOwner, Administrator, AccountRole
from server.app.models.team import Team, team_manager_team
from server.app.decorators.login_required import login_required

team_bp = Blueprint("team", __name__, url_prefix="/api/teams")

#  Helpers

def _get_team_or_404(team_id: int):
  team = Team.query.get(team_id)
  if not team:
    return None, (jsonify({"message": "Team not found."}), 404)
  return team, None


def _can_edit_team(resolved, team: Team) -> bool:
  """
  Administrator - any team
  ClubOwner - teams of his club OR teams without a club he manages as a manager
  TeamManager - only teams without a club that he manages
  """

  if isinstance(resolved, Administrator):
    return True

  team_without_club = team.club_id is None

  if isinstance(resolved, ClubOwner):
    manages_team = team in resolved.team_manager.teams
    owns_club    = team.club is not None and team.club in resolved.clubs
    return owns_club or (manages_team and team_without_club)

  if isinstance(resolved, TeamManager):
    manages_team = team in resolved.team_manager.teams
    return manages_team and team_without_club
  return False


def _resolve_target(account_id: int):
  """Retrieves the target Account or returns an error."""
  if not account_id:
    return None, (jsonify({"message": "Field 'accountId' is required."}), 422)
  target = Account.query.get(account_id)
  if not target:
    return None, (jsonify({"message": "Account not found."}), 404)
  return target, None

def _handle_team_after_last_manager_removed(team: Team):
  """
  Called when the last manager is removed from a team WITHOUT a club.
  Promotes a random player to manager, or removes the team.
  """
  if team.club_id is not None:
    return  # we don't touch the team with the club

  # This ensures that we are reading the current state of the database, not the SQLAlchemy cache.
  remaining_count = db.session.execute(
    db.select(db.func.count()).select_from(team_manager_team).where(
      team_manager_team.c.team_id == team.id
    )
  ).scalar()

  if remaining_count > 0:
    return # there are still managers

  if team.players:
    # Promote a random player to TeamManager
    random_player = team.players[0]
    account = random_player.account

    tm_role = AccountRole.query.filter_by(name="team_manager").first()
    new_tm = TeamManager(id=account.id)
    db.session.add(new_tm)
    account.account_role_id = tm_role.id
    db.session.flush()

    account.team_manager.teams.append(team)
  else:
    # There is no one - delete the team
    db.session.delete(team)

def _parse_pagination(args):
  """
  Extracts pagination parameters from query string.
  ?from=0&to=20&sort=name|id
  Returns (offset, limit, sort_col, error)
  """
  try:
    offset = int(args.get("from", 0))
    to     = int(args.get("to",   20))
  except ValueError:
    return None, None, None, (jsonify({"message": "'from' and 'to' must be integers."}), 422)

  if offset < 0 or to < offset:
    return None, None, None, (jsonify({"message": "'from' must be >= 0 and 'to' must be >= 'from'."}), 422)

  limit = to - offset

  sort = args.get("sort", "id")
  if sort == "name":
    sort_col = Team.name.asc()
  elif sort == "id":
    sort_col = Team.id.asc()
  else:
    return None, None, None, (jsonify({"message": "'sort' must be 'id' or 'name'."}), 422)

  return offset, limit, sort_col, None

#  GET TEAM BY ID

@team_bp.route("/<int:team_id>", methods=["GET"])
def get_team(team_id: int):
  team, err = _get_team_or_404(team_id)
  if err:
    return err

  return jsonify({"team": team.to_dict()}), 200

#  GET ALL TEAMS

@team_bp.route("", methods=["GET"])
def get_teams():
  """
  GET /api/teams?from=0&to=20&sort=name
  Public. Returns a slice of teams from total for pagination on the front.
  """
  offset, limit, sort_col, err = _parse_pagination(request.args)
  if err:
    return err

  base_query = Team.query

  total = base_query.count()
  teams = base_query.order_by(sort_col).offset(offset).limit(limit).all()

  return jsonify({
    "total": total,
    "from":  offset,
    "to":    offset + len(teams),
    "teams": [t.to_dict() for t in teams],
  }), 200


#  GET TEAMS BY CLUB

@team_bp.route("/by-club/<int:club_id>", methods=["GET"])
def get_teams_by_club(club_id: int):
  """
  GET /api/teams/by-club/<club_id>?from=0&to=20&sort=name
  Public.
  """
  from server.app.models.club import Club

  club = Club.query.get(club_id)
  if not club:
    return jsonify({"message": "Club not found."}), 404

  offset, limit, sort_col, err = _parse_pagination(request.args)
  if err:
    return err

  base_query = Team.query.filter_by(club_id=club_id)

  total = base_query.count()
  teams = base_query.order_by(sort_col).offset(offset).limit(limit).all()

  return jsonify({
    "clubId": club_id,
    "total":  total,
    "from":   offset,
    "to":     offset + len(teams),
    "teams":  [t.to_dict() for t in teams],
  }), 200


#  GET TEAMS MANAGED BY CURRENT USER

@team_bp.route("/my", methods=["GET"])
@login_required
def get_my_teams(user: Account):
  """
  GET /api/teams/my?from=0&to=20&sort=name
  Returns the teams managed by the current user.
  Administrator sees all teams.
  ClubOwner sees the teams of his clubs + the teams he manages as a manager.
  TeamManager sees the teams he manages.
  Others - an empty list.
  """
  offset, limit, sort_col, err = _parse_pagination(request.args)
  if err:
    return err

  resolved = user.resolved_role

  if isinstance(resolved, Administrator):
    base_query = Team.query

  elif isinstance(resolved, ClubOwner):
    # ID of clubs owned
    club_ids = [c.id for c in resolved.clubs]
    # ID of the teams managed as a manager
    managed_ids = [t.id for t in resolved.team_manager.teams]

    base_query = Team.query.filter(
      db.or_(
        Team.club_id.in_(club_ids),
        Team.id.in_(managed_ids),
      )
    )

  elif isinstance(resolved, TeamManager):
    managed_ids = [t.id for t in resolved.teams]
    base_query = Team.query.filter(Team.id.in_(managed_ids))

  else:
    return jsonify({
      "total": 0,
      "from":  offset,
      "to":    offset,
      "teams": [],
    }), 200

  total = base_query.count()
  teams = base_query.order_by(sort_col).offset(offset).limit(limit).all()

  return jsonify({
    "total": total,
    "from":  offset,
    "to":    offset + len(teams),
    "teams": [t.to_dict() for t in teams],
  }), 200

#  CREATE TEAM

@team_bp.route("", methods=["POST"])
@login_required
def create_team(user: Account):
  data = request.get_json(silent=True)
  if not data:
    return jsonify({"message": "No JSON body provided."}), 400

  name = data.get("name", "").strip()
  if not name:
    return jsonify({"message": "Field 'name' is required."}), 422

  club_id       = data.get("clubId")
  sport_type_id = data.get("sportTypeId")

  resolved = user.resolved_role

  if isinstance(resolved, Administrator):
    acting_manager = None
  elif isinstance(resolved, (ClubOwner, TeamManager)):
    acting_manager = user.team_manager
  else:
    err = promote_to_team_manager(user)
    if err:
      return err
    acting_manager = user.team_manager  # after refresh - no longer None
    if acting_manager is None:
      return jsonify({"message": "Failed to initialize team manager."}), 500

  if club_id is not None:
    existing = Team.query.filter_by(club_id=club_id, name=name).first()
    if existing:
      return jsonify({"message": "A team with this name already exists in the club."}), 409

  new_team = Team(name=name, club_id=club_id, sport_type_id=sport_type_id)
  db.session.add(new_team)
  db.session.flush()

  if acting_manager is not None:
    acting_manager.teams.append(new_team)

  db.session.commit()

  return jsonify({
    "message": "Team created successfully.",
    "team": new_team.to_dict()
  }), 201

#  ADD MANAGER TO TEAM

@team_bp.route("/<int:team_id>/managers", methods=["POST"])
@login_required
def add_manager_to_team(user: Account, team_id: int):
  team, err = _get_team_or_404(team_id)
  if err:
    return err

  if not _can_edit_team(user.resolved_role, team):
    return jsonify({"message": "Forbidden."}), 403

  data = request.get_json(silent=True)
  if not data:
    return jsonify({"message": "No JSON body provided."}), 400

  target, err = _resolve_target(data.get("accountId"))
  if err:
    return err

  if isinstance(target.resolved_role, Administrator):
    return jsonify({"message": "Cannot assign Administrator as a team manager."}), 422

  err = promote_to_team_manager(target)
  if err:
    return err

  if team in target.team_manager.teams:
    return jsonify({"message": "This account is already a manager of this team."}), 409

  target.team_manager.teams.append(team)
  db.session.commit()

  return jsonify({
    "message": "Manager added successfully.",
    "manager": target.team_manager.to_dict(),
  }), 200

@team_bp.route("/<int:team_id>/players", methods=["POST"])
@login_required
def add_player_to_team(user: Account, team_id: int):
  team, err = _get_team_or_404(team_id)
  if err:
    return err

  if not _can_edit_team(user.resolved_role, team):
    return jsonify({"message": "Forbidden."}), 403

  data = request.get_json(silent=True)
  if not data:
    return jsonify({"message": "No JSON body provided."}), 400

  target, err = _resolve_target(data.get("accountId"))
  if err:
    return err

  if isinstance(target.resolved_role, (Administrator, TeamManager, ClubOwner)):
    return jsonify({"message": "Cannot assign this role as a player."}), 422

  err = promote_to_player(target)
  if err:
    return err

  if team in target.player.teams:
    return jsonify({"message": "This account is already a player in this team."}), 409

  target.player.teams.append(team)
  db.session.commit()

  return jsonify({
    "message": "Player added successfully.",
    "player": target.player.to_dict(),
  }), 200

#  REMOVE MANAGER FROM TEAM

@team_bp.route("/<int:team_id>/managers/<int:account_id>", methods=["DELETE"])
@login_required
def remove_manager_from_team(user: Account, team_id: int, account_id: int):
  team, err = _get_team_or_404(team_id)
  if err:
    return err

  if not _can_edit_team(user.resolved_role, team):
    return jsonify({"message": "Forbidden."}), 403

  target, err = _resolve_target(account_id)
  if err:
    return err

  if not target.team_manager or team not in target.team_manager.teams:
    return jsonify({"message": "This account is not a manager of this team."}), 404

  target.team_manager.teams.remove(team)
  db.session.flush()

  _handle_team_after_last_manager_removed(team)

  db.session.commit()

  return jsonify({"message": "Manager removed successfully."}), 200

#  REMOVE PLAYER FROM TEAM

@team_bp.route("/<int:team_id>/players/<int:account_id>", methods=["DELETE"])
@login_required
def remove_player_from_team(user: Account, team_id: int, account_id: int):
  team, err = _get_team_or_404(team_id)
  if err:
    return err

  if not _can_edit_team(user.resolved_role, team):
    return jsonify({"message": "Forbidden."}), 403

  target, err = _resolve_target(account_id)
  if err:
    return err

  if not target.player or team not in target.player.teams:
    return jsonify({"message": "This account is not a player in this team."}), 404

  target.player.teams.remove(team)
  db.session.commit()

  return jsonify({"message": "Player removed successfully."}), 200


#  DELETE TEAM

@team_bp.route("/<int:team_id>", methods=["DELETE"])
@login_required
def delete_team(user: Account, team_id: int):
  team, err = _get_team_or_404(team_id)
  if err:
    return err

  if not _can_edit_team(user.resolved_role, team):
    return jsonify({"message": "Forbidden."}), 403

  db.session.delete(team)
  db.session.commit()

  return jsonify({"message": "Team deleted successfully."}), 200

#  RENAME TEAM

@team_bp.route("/<int:team_id>", methods=["PATCH"])
@login_required
def rename_team(user: Account, team_id: int):
  team, err = _get_team_or_404(team_id)
  if err:
    return err

  if not _can_edit_team(user.resolved_role, team):
    return jsonify({"message": "Forbidden."}), 403

  data = request.get_json(silent=True)
  if not data:
    return jsonify({"message": "No JSON body provided."}), 400

  name = data.get("name", "").strip()
  if not name:
    return jsonify({"message": "Field 'name' is required."}), 422

  if name == team.name:
    return jsonify({"message": "New name is the same as current."}), 422

  # Check uniqueness (club_id, name)
  if team.club_id is not None:
    existing = Team.query.filter_by(club_id=team.club_id, name=name).first()
    if existing:
      return jsonify({"message": "A team with this name already exists in the club."}), 409

  team.name = name
  db.session.commit()

  return jsonify({
    "message": "Team renamed successfully.",
    "team": team.to_dict()
  }), 200