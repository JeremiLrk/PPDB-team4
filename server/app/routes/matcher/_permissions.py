from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import Team, TeamManager


def _can_create_match(resolved, team1: Team, team2: Team) -> bool:
    """
    Allowed if resolved:
      - is Administrator, OR
      - is ClubOwner with can_create_match on either team's club, OR
      - is TeamManager of team1 OR team2.
    """
    if isinstance(resolved, Administrator):
        return True

    if isinstance(resolved, ClubOwner):
        for team in (team1, team2):
            if team.club is not None:
                assoc = resolved.assoc_for(team.club)
                if assoc and assoc.can_create_match:
                    return True
        return False

    if isinstance(resolved, TeamManager):
        managed_ids = {a.team_id for a in resolved.team_associations}
        return team1.id in managed_ids or team2.id in managed_ids

    return False