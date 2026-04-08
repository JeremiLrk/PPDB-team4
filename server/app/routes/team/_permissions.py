from flask import abort

from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import Team, TeamManagerTeam, TeamManager


def _get_manager_assoc(resolved, team: Team) -> TeamManagerTeam | None:
    """
    Returns the TeamManagerTeam record for the resolved user relative to the team,
    or None if the resolved user is not the manager of that team.
    """
    if not isinstance(resolved, TeamManager):
        return None
    return next(
        (a for a in resolved.team_associations if a.team_id == team.id),
        None
    )


def _is_admin_or_club_owner_of(resolved, team: Team) -> bool:
    """
    Returns True if resolved is an Administrator
    or the ClubOwner who owns the team's club.
    """
    if isinstance(resolved, Administrator):
        return True
    if isinstance(resolved, ClubOwner):
        return team.club is not None and team.club in resolved.clubs
    return False

def _can_rename_or_403(resolved, team: Team) -> None:
    """
    """
    if not _can_rename(resolved, team):
        abort(403, description="Forbidden.")
    return None


def _can_rename(resolved, team: Team) -> bool:
    """
    Administrator or ClubOwner (club owner) — always.
    TeamManager — only if can_rename=True in the association.
    """
    if _is_admin_or_club_owner_of(resolved, team):
        return True
    assoc = _get_manager_assoc(resolved, team)
    return assoc is not None and assoc.can_rename


def _can_delete_or_403(resolved, team: Team) -> None:
    """
    """
    if not _can_delete(resolved, team):
        abort(403, description="Forbidden.")
    return None

def _can_delete(resolved, team: Team) -> bool:
    """
    Administrator or ClubOwner (club owner) — always.
    TeamManager — only if can_delete=True in the association.
    """
    if _is_admin_or_club_owner_of(resolved, team):
        return True
    assoc = _get_manager_assoc(resolved, team)
    return assoc is not None and assoc.can_delete


def _can_edit_players_or_403(resolved, team: Team) -> None:
    """
    """
    if not _can_edit_players(resolved, team):
        abort(403, description="Forbidden.")
    return None


def _can_edit_players(resolved, team: Team) -> bool:
    """
    Administrator or ClubOwner (club owner) — always.
    TeamManager — only if can_edit_players=True in the association.
    """
    if _is_admin_or_club_owner_of(resolved, team):
        return True
    assoc = _get_manager_assoc(resolved, team)
    return assoc is not None and assoc.can_edit_players


def _can_edit_managers_or_403(resolved, team: Team) -> None:
    """
    """
    if not _can_edit_managers(resolved, team):
        abort(403, description="Forbidden.")
    return None

def _can_edit_managers(resolved, team: Team) -> bool:
    """
    Administrator or ClubOwner (club owner) — always.
    TeamManager — only if can_edit_managers=True in the association.
    """
    if _is_admin_or_club_owner_of(resolved, team):
        return True
    assoc = _get_manager_assoc(resolved, team)
    return assoc is not None and assoc.can_edit_managers