"""
Backward-compatible helpers for legacy tests/imports.

The current team implementation lives under `server.app.routes.team.*`.
This module keeps older helper signatures available.
"""

from flask import jsonify

from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import TeamManager


def parse_pagination(args):
    """Parse the legacy team pagination arguments."""
    try:
        offset = int(args.get("from", 0))
        to = int(args.get("to", 20))
    except ValueError:
        return None, None, None, (jsonify({"message": "'from' and 'to' must be integers."}), 422)

    if offset < 0 or to < offset:
        return None, None, None, (jsonify({"message": "'from' must be >= 0 and 'to' must be >= 'from'."}), 422)

    limit = to - offset

    sort = args.get("sort", "id")
    if sort == "name":
        from server.app.models.team import Team

        sort_col = Team.name.asc()
    elif sort == "id":
        from server.app.models.team import Team

        sort_col = Team.id.asc()
    else:
        return None, None, None, (jsonify({"message": "'sort' must be 'id' or 'name'."}), 422)

    return offset, limit, sort_col, None


def can_edit_team(resolved, team):
    """Return whether the legacy edit helper allows access."""
    if isinstance(resolved, Administrator):
        return True
    if isinstance(resolved, ClubOwner):
        return team.club is not None and team.club in resolved.clubs
    if isinstance(resolved, TeamManager):
        # Legacy behavior: team managers may edit teams they manage only when
        # the team has no club owner context.
        return team in resolved.teams and team.club_id is None
    return False


# Compatibility aliases for older imports and tests.
_parse_pagination = parse_pagination
_can_edit_team = can_edit_team
