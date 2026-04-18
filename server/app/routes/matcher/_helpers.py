from flask import abort

from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import Team, TeamManager
from server.app.models.match import (
    MatchProposal,
)

# ===========================================================================
# Internal helpers
# ===========================================================================

def _get_proposal_or_404(match_id: int) -> MatchProposal:
    proposal = MatchProposal.query.get(match_id)
    if not proposal:
        abort(404, description="Match proposal not found.")
    return proposal


def _get_team_or_404(team_id: int) -> Team:
    team = Team.query.get(team_id)
    if not team:
        abort(404, description=f"Team {team_id} not found.")
    return team


def _manages_team(resolved, team: Team) -> bool:
    """True if *resolved* is an Administrator, a ClubOwner of the team's club,
    or a TeamManager explicitly assigned to *team*."""
    if isinstance(resolved, Administrator):
        return True
    if isinstance(resolved, ClubOwner):
        return team.club is not None and team.club in resolved.clubs
    if isinstance(resolved, TeamManager):
        return any(a.team_id == team.id for a in resolved.team_associations)
    return False



def _parse_pagination(args):
    try:
        offset = int(args.get("from", 0))
        to     = int(args.get("to",   20))
    except ValueError:
        abort(422, description="'from' and 'to' must be integers.")

    if offset < 0 or to < offset:
        abort(422, description="'from' must be >= 0 and 'to' must be >= 'from'.")
    return offset, to - offset


def _team_ids_managed_by(resolved) -> set[int] | None:
    """Returns the set of team IDs the resolved role manages."""
    if isinstance(resolved, Administrator):
        # Admin sees everything — return sentinel
        return None  # handled by callers
    if isinstance(resolved, ClubOwner):
        ids: set[int] = set()
        for club in resolved.clubs:
            for team in club.teams:
                ids.add(team.id)
        # also directly managed teams via team_manager parent
        tm = resolved.team_manager
        for a in tm.team_associations:
            ids.add(a.team_id)
        return ids
    if isinstance(resolved, TeamManager):
        return {a.team_id for a in resolved.team_associations}
    return set()