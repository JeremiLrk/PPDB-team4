"""
Permission helpers for matcher routes.

The matcher endpoints use the same team-management rules as the rest of the
app, so this module keeps the checks in one place.
"""

from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import Team, TeamManager


def can_manage_match(resolved, team: Team) -> bool:
    """Return whether the resolved role may manage matches for a team."""
    if isinstance(resolved, Administrator):
        return True

    if isinstance(resolved, ClubOwner):
        return team.club is not None and team.club in resolved.clubs

    if isinstance(resolved, TeamManager):
        return resolved.can_manage_match_in(team)
    return False

def can_manage_either_team(resolved, team1: Team, team2: Team) -> bool:
    """Return whether the resolved role may manage at least one side."""
    if isinstance(resolved, Administrator):
        return True
    return can_manage_match(resolved, team1) or can_manage_match(resolved, team2)
