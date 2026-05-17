"""
Shared helpers for matcher routes.

These utilities keep the match-list and match-detail endpoints aligned on the
same lookup and pagination rules.
"""

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

def get_proposal_or_404(match_id: int) -> MatchProposal:
    """Load a match proposal or abort with 404 if it is missing."""
    proposal = MatchProposal.query.get(match_id)
    if not proposal:
        abort(404, description="Match proposal not found.")
    return proposal


def get_team_or_404(team_id: int) -> Team:
    """Load a team or abort with 404 if it does not exist."""
    team = Team.query.get(team_id)
    if not team:
        abort(404, description=f"Team {team_id} not found.")
    return team


def parse_pagination(args):
    """Parse the shared from/to pagination arguments."""
    try:
        offset = int(args.get("from", 0))
        to     = int(args.get("to",   20))
    except ValueError:
        abort(422, description="'from' and 'to' must be integers.")

    if offset < 0 or to < offset:
        abort(422, description="'from' must be >= 0 and 'to' must be >= 'from'.")
    return offset, to - offset


def team_ids_managed_by(resolved) -> set[int] | None:
    """Return the set of team ids managed by the resolved role."""
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
