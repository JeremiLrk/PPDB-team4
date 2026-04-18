"""
Permission helpers for team routes.

Design:
  - `_can_*`           — pure boolean functions (composable, testable)
  - `_can_*_or_403`    — abort(403) wrappers for use in route handlers
  - `require_*`        — @decorator versions for the same checks

Usage in routes:
    # decorator style
    @core_bp.route("/<int:team_id>", methods=["DELETE"])
    @login_required
    @require_can_delete_team
    def delete_team(account: Account, team_id: int): ...

    # explicit call style
    _can_delete_or_403(account.resolved_role, team)
"""

from functools import wraps
from flask import abort

from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import Team, TeamManagerTeam, TeamManager


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_manager_assoc(resolved, team: Team) -> TeamManagerTeam | None:
    """
    Returns the TeamManagerTeam record for *resolved* relative to *team*,
    or None if resolved is not a manager of that team.
    """
    if not isinstance(resolved, TeamManager):
        return None
    return next(
        (a for a in resolved.team_associations if a.team_id == team.id),
        None,
    )


def _is_admin_or_club_owner_of(resolved, team: Team) -> bool:
    """True if resolved is an Administrator, or a ClubOwner of the team's club."""
    if isinstance(resolved, Administrator):
        return True
    if isinstance(resolved, ClubOwner):
        return team.club is not None and team.club in resolved.clubs
    return False


# ---------------------------------------------------------------------------
# Boolean permission functions
# ---------------------------------------------------------------------------

def _can_rename(resolved, team: Team) -> bool:
    if _is_admin_or_club_owner_of(resolved, team):
        return True
    if isinstance(resolved, TeamManager):
        return resolved.can_rename_team(team)
    return False


def _can_delete(resolved, team: Team) -> bool:
    if _is_admin_or_club_owner_of(resolved, team):
        return True
    if isinstance(resolved, TeamManager):
        return resolved.can_delete_team(team)
    return False


def _can_edit_players(resolved, team: Team) -> bool:
    if _is_admin_or_club_owner_of(resolved, team):
        return True
    if isinstance(resolved, TeamManager):
        return resolved.can_edit_players_of(team)
    return False


def _can_edit_managers(resolved, team: Team) -> bool:
    if _is_admin_or_club_owner_of(resolved, team):
        return True
    if isinstance(resolved, TeamManager):
        return resolved.can_edit_managers_of(team)
    return False


# ---------------------------------------------------------------------------
# abort(403) wrappers
# ---------------------------------------------------------------------------

def _can_rename_or_403(resolved, team: Team) -> None:
    if not _can_rename(resolved, team):
        abort(403, description="Forbidden: cannot rename this team.")


def _can_delete_or_403(resolved, team: Team) -> None:
    if not _can_delete(resolved, team):
        abort(403, description="Forbidden: cannot delete this team.")


def _can_edit_players_or_403(resolved, team: Team) -> None:
    if not _can_edit_players(resolved, team):
        abort(403, description="Forbidden: cannot edit players of this team.")


def _can_edit_managers_or_403(resolved, team: Team) -> None:
    if not _can_edit_managers(resolved, team):
        abort(403, description="Forbidden: cannot edit managers of this team.")


# ---------------------------------------------------------------------------
# Decorator factory
# ---------------------------------------------------------------------------

def _make_team_permission_decorator(check_fn, *, team_id_kwarg: str = "team_id"):
    """
    Returns a decorator that:
      1. Reads `team_id` from the route kwargs.
      2. Loads the Team (404 if missing).
      3. Calls `check_fn(resolved, team)` and aborts 403 on failure.
    The decorated view still receives `account` as its first argument
    (injected by @login_required) and `team_id` in kwargs.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(account, *args, **kwargs):
            from server.app.routes.team._helpers import _get_team_or_404
            team_id = kwargs.get(team_id_kwarg)
            if team_id is None:
                abort(400, description=f"Missing URL parameter '{team_id_kwarg}'.")
            team = _get_team_or_404(team_id)
            if not check_fn(account.resolved_role, team):
                abort(403, description="Forbidden.")
            return f(account, *args, **kwargs)
        return wrapper
    return decorator


require_can_rename_team = _make_team_permission_decorator(_can_rename)
require_can_delete_team = _make_team_permission_decorator(_can_delete)
require_can_edit_players = _make_team_permission_decorator(_can_edit_players)
require_can_edit_managers = _make_team_permission_decorator(_can_edit_managers)


# ---------------------------------------------------------------------------
# Permissions dict (used by GET endpoints to expose capabilities to the UI)
# ---------------------------------------------------------------------------

def _get_permissions(resolved, team: Team) -> dict:
    if _is_admin_or_club_owner_of(resolved, team):
        return {
            "canRename":       True,
            "canDelete":       True,
            "canEditPlayers":  True,
            "canEditManagers": True,
        }
    assoc = _get_manager_assoc(resolved, team)
    if assoc is None:
        return {
            "canRename":       False,
            "canDelete":       False,
            "canEditPlayers":  False,
            "canEditManagers": False,
        }
    return {
        "canRename":       assoc.can_rename,
        "canDelete":       assoc.can_delete,
        "canEditPlayers":  assoc.can_edit_players,
        "canEditManagers": assoc.can_edit_managers,
    }
