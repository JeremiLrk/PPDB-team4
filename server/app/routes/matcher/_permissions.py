from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import Team, TeamManager


def _can_manage_match(resolved, team: Team) -> bool:
    """True if *resolved* is an Administrator, a ClubOwner of the team's club,
    or a TeamManager explicitly assigned to *team*."""
    if isinstance(resolved, Administrator):
        return True

    if isinstance(resolved, ClubOwner):
        return team.club is not None and team.club in resolved.clubs

    if isinstance(resolved, TeamManager):
        return resolved.can_manage_match_in(team)
    return False

def _can_manage_either_team(resolved, team1: Team, team2: Team) -> bool:
    """True if *resolved* can manage at least one of the two teams.
    Used for proposal creation: the initiating side must manage team1 or team2.
    Administrator always passes.
    """
    if isinstance(resolved, Administrator):
        return True
    return _can_manage_match(resolved, team1) or _can_manage_match(resolved, team2)
