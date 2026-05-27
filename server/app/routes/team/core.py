"""
Core team routes.

These endpoints cover public team lookup plus create, rename, and delete
operations for the team management UI.
"""

from flask import Blueprint, request, jsonify, abort
from server.extensions import cache, db
from server.app.models.account import Account, Administrator
from server.app.models.team import Team, TeamManagerTeam, TeamManager
from server.app.decorators.login_required import login_required
from server.app.utils.promote import promote_to_team_manager
from ._helpers import get_team_or_404, parse_pagination, delete_teams_cache_keys
from ._permissions import require_can_delete_team, require_can_rename_team
from ...models.club_owner import ClubOwner

core_bp = Blueprint("team_core", __name__)


@core_bp.route("/<int:team_id>", methods=["GET"])
@cache.memoize(timeout=300)
def get_team(team_id: int):
    """Return one public team record."""
    team = get_team_or_404(team_id)
    return jsonify({
        "team": team.to_dict()
    }), 200


@core_bp.route("", methods=["GET"])
@cache.cached(timeout=300, query_string=True, key_prefix="teams_list")
def get_teams():
    """Return the public team list."""
    offset, limit, sort_col =  parse_pagination(request.args)

    total = Team.query.count()
    teams = Team.query.order_by(sort_col).offset(offset).limit(limit).all()

    return jsonify({
        "total": total,
        "from":  offset,
        "to":    offset + len(teams),
        "teams": [t.to_dict() for t in teams],
    }), 200

# Not used anywhere?
@core_bp.route("/by-club/<int:club_id>", methods=["GET"])
def get_teams_by_club(club_id: int):
    """Return public teams for a specific club."""
    from server.app.models.club import Club
    club = Club.query.get(club_id)
    if not club:
        abort(404, description="Club not found.")

    offset, limit, sort_col = parse_pagination(request.args)

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


@core_bp.route("", methods=["POST"])
@login_required
def create_team(account: Account):
    """
    Create a new team and attach the acting manager when needed.

    Args:
        account (Account): The account creating the team.

    Returns:
        tuple: A tuple containing the response and status code.
    """
    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    name = data.get("name", "").strip()
    if not name:
        abort(422, description="Field 'name' is required.")

    club_id = data.get("clubId")

    existing = db.session.query(Team).filter_by(
        name=name,
        club_id=club_id
    ).first()

    if existing:
        abort(400, description="Team with this name already exists.")

    sport_type_id = data.get("sportTypeId")
    resolved = account.resolved_role

    if isinstance(resolved, Administrator):
        acting_manager = None
    elif isinstance(resolved, (ClubOwner, TeamManager)):
        acting_manager = account.team_manager
    else:
        promote_to_team_manager(account)
        acting_manager = account.team_manager

    if club_id is not None:
        if Team.query.filter(Team.club_id == club_id, Team.name == name).first():
            abort(409, description="A team with this name already exists in the club.")

    new_team = Team(name=name, club_id=club_id, sport_type_id=sport_type_id)
    db.session.add(new_team)
    db.session.flush()

    if acting_manager is not None:
        assoc = TeamManagerTeam(
            team_manager_id=acting_manager.id,
            team_id=new_team.id,
            can_rename=True,
            can_delete=True,
            can_edit_players=True,
            can_edit_managers=True,
            can_manage_match=True,
        )
        db.session.add(assoc)

    delete_teams_cache_keys()

    db.session.commit()
    return jsonify({
        "message": "Team created successfully.",
        "team": new_team.to_dict()
    }), 201


@core_bp.route("/<int:team_id>", methods=["DELETE"])
@login_required
@require_can_delete_team
def delete_team(account: Account, team_id: int):
    """
    Delete a team if the user has permission.

    Preconditions:
        - `account` must exist and be active in the database.

    Args:
        account (Account): The account attempting to delete the team.
        team_id (int): The unique identifier of the team to delete.

    Returns:
        a JSON response containing a success message, along with a 200 status code.

    Postconditions:
        - The specified team is deleted from the database if the user has permission.
    """
    team = get_team_or_404(team_id)

    db.session.delete(team)
    db.session.commit()

    cache.delete_memoized(get_team, team_id)
    delete_teams_cache_keys()

    return jsonify({
        "message": "Team deleted successfully."
    }), 200


@core_bp.route("/<int:team_id>", methods=["PATCH"])
@login_required
@require_can_rename_team
def rename_team(account: Account, team_id: int):
    """
    Rename a team if the user has permission.

    Preconditions:
        - `account` must exist and be active in the database.

    Args:
        account (Account): The account attempting to rename the team.
        team_id (int): The unique identifier of the team to rename.

    Returns:
        a JSON response containing a success message, along with a 200 status code.

    Postconditions:
        - The specified team is renamed in the database if the user has permission.
    """
    team = get_team_or_404(team_id)

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="No JSON body provided.")

    name = data.get("name", "").strip()
    if not name:
        abort(422, description="Field 'name' is required.")
    if name == team.name:
        abort(422, description="New name is the same as current.")

    if team.club_id is not None:
        if Team.query.filter(
            Team.club_id == team.club_id,
            Team.name == name,
            Team.id != team.id,
        ).first():
            abort(409, description="A team with this name already exists in the club.")

    team.name = name
    db.session.commit()

    cache.delete_memoized(get_team, team_id)
    delete_teams_cache_keys()

    return jsonify({
        "message": "Team renamed successfully.",
        "team": team.to_dict()
    }), 200
