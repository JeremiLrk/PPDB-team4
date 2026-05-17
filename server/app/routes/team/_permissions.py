"""
Permission helpers for team routes.

Design:
  - `can_*`            — pure boolean functions (composable, testable)
  - `can_*_or_403`     — abort(403) wrappers for use in route handlers
  - `require_*`        — @decorator versions for the same checks

Usage in routes:
    # decorator style
    @core_bp.route("/<int:team_id>", methods=["DELETE"])
    @login_required
    @require_can_delete_team
    def delete_team(account: Account, team_id: int): ...

    # explicit call style
    can_delete_or_403(account.resolved_role, team)
"""

from functools import wraps
from flask import abort

from server.app.models.account import Administrator
from server.app.models.club_owner import ClubOwner
from server.app.models.team import Team, TeamManagerTeam, TeamManager


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def get_manager_assoc(resolved, team: Team) -> TeamManagerTeam | None:
    """Return the manager-team association for the resolved role, if any."""
    if isinstance(resolved, ClubOwner):
        tm = resolved.team_manager
        if tm is None:
            return None
        return next(
            (a for a in tm.team_associations if a.team_id == team.id),
            None,
        )
    if isinstance(resolved, TeamManager):
        return next(
            (a for a in resolved.team_associations if a.team_id == team.id),
            None,
        )
    return None


def is_admin(resolved) -> bool:
    """Return whether the resolved role is an administrator."""
    return isinstance(resolved, Administrator)


def is_owner_of_team_club(resolved, team: Team) -> bool:
    """Return whether the resolved role owns the club that hosts the team."""
    return (
        isinstance(resolved, ClubOwner)
        and team.club is not None
        and team.club in resolved.clubs
    )


# ---------------------------------------------------------------------------
# Boolean permission functions
# ---------------------------------------------------------------------------

def can_rename(resolved, team: Team) -> bool:
    """Return whether the resolved role may rename the team."""
    if is_admin(resolved) or is_owner_of_team_club(resolved, team):
        return True
    # ClubOwner is NOT a Python subclass of TeamManager — delegate via back-ref
    if isinstance(resolved, ClubOwner):
        tm = resolved.team_manager
        return tm is not None and tm.can_rename_team(team)
    if isinstance(resolved, TeamManager):
        return resolved.can_rename_team(team)
    return False


def can_delete(resolved, team: Team) -> bool:
    """Return whether the resolved role may delete the team."""
    if is_admin(resolved) or is_owner_of_team_club(resolved, team):
        return True
    if isinstance(resolved, ClubOwner):
        tm = resolved.team_manager
        return tm is not None and tm.can_delete_team(team)
    if isinstance(resolved, TeamManager):
        return resolved.can_delete_team(team)
    return False


def can_edit_players(resolved, team: Team) -> bool:
    """Return whether the resolved role may edit team players."""
    if is_admin(resolved) or is_owner_of_team_club(resolved, team):
        return True
    if isinstance(resolved, ClubOwner):
        tm = resolved.team_manager
        return tm is not None and tm.can_edit_players_of(team)
    if isinstance(resolved, TeamManager):
        return resolved.can_edit_players_of(team)
    return False


def can_edit_managers(resolved, team: Team) -> bool:
    """Return whether the resolved role may edit team managers."""
    if is_admin(resolved) or is_owner_of_team_club(resolved, team):
        return True
    if isinstance(resolved, ClubOwner):
        tm = resolved.team_manager
        return tm is not None and tm.can_edit_managers_of(team)
    if isinstance(resolved, TeamManager):
        return resolved.can_edit_managers_of(team)
    return False


# ---------------------------------------------------------------------------
# abort(403) wrappers
# ---------------------------------------------------------------------------

def can_rename_or_403(resolved, team: Team) -> None:
    """Abort with 403 unless the resolved role may rename the team."""
    if not can_rename(resolved, team):
        abort(403, description="Forbidden: cannot rename this team.")


def can_delete_or_403(resolved, team: Team) -> None:
    """Abort with 403 unless the resolved role may delete the team."""
    if not can_delete(resolved, team):
        abort(403, description="Forbidden: cannot delete this team.")


def can_edit_players_or_403(resolved, team: Team) -> None:
    """Abort with 403 unless the resolved role may edit players."""
    if not can_edit_players(resolved, team):
        abort(403, description="Forbidden: cannot edit players of this team.")


def can_edit_managers_or_403(resolved, team: Team) -> None:
    """Abort with 403 unless the resolved role may edit managers."""
    if not can_edit_managers(resolved, team):
        abort(403, description="Forbidden: cannot edit managers of this team.")


# ---------------------------------------------------------------------------
# Decorator factory
# ---------------------------------------------------------------------------

def make_team_permission_decorator(check_fn, *, team_id_kwarg: str = "team_id"):
    """Build a route decorator that loads the team and applies a permission check."""
    def decorator(f):
        @wraps(f)
        def wrapper(account, *args, **kwargs):
            from server.app.routes.team._helpers import get_team_or_404
            team_id = kwargs.get(team_id_kwarg)
            if team_id is None:
                abort(400, description=f"Missing URL parameter '{team_id_kwarg}'.")
            team = get_team_or_404(team_id)
            if not check_fn(account.resolved_role, team):
                # The decorator handles the 403 so route code can stay linear.
                abort(403, description="Forbidden.")
            return f(account, *args, **kwargs)
        return wrapper
    return decorator


require_can_rename_team   = make_team_permission_decorator(can_rename)
require_can_delete_team   = make_team_permission_decorator(can_delete)
require_can_edit_players  = make_team_permission_decorator(can_edit_players)
require_can_edit_managers = make_team_permission_decorator(can_edit_managers)


# ---------------------------------------------------------------------------
# Permissions dict (used by GET endpoints to expose capabilities to the UI)
# ---------------------------------------------------------------------------

def get_permissions(resolved, team: Team) -> dict:
    """Return the editable team permission flags for the resolved role."""
    if is_admin(resolved) or is_owner_of_team_club(resolved, team):
        return {
            "canRename":       True,
            "canDelete":       True,
            "canEditPlayers":  True,
            "canEditManagers": True,
        }
    assoc = get_manager_assoc(resolved, team)
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

# ---------------------------------------------------------------------------
# Join-request permissions
# ---------------------------------------------------------------------------

def can_manage_join_request(resolved, join_request, team: Team) -> bool:
    """Return whether the resolved role may manage a team join request."""
    if is_admin(resolved):
        return True

    if join_request.user_id == resolved.id:
        # Users can still manage their own request record in this flow.
        return True

    return False


def can_manage_join_request_or_403(resolved, join_request, team: Team) -> None:
    """Abort with 403 unless the resolved role may manage the join request."""
    if not can_manage_join_request(resolved, join_request, team):
        abort(403, description="Forbidden: cannot manage join requests for this team.")


# Compatibility aliases for older imports and tests.
_get_manager_assoc = get_manager_assoc
_is_admin = is_admin
_is_owner_of_team_club = is_owner_of_team_club
_can_rename = can_rename
_can_delete = can_delete
_can_edit_players = can_edit_players
_can_edit_managers = can_edit_managers
_can_rename_or_403 = can_rename_or_403
_can_delete_or_403 = can_delete_or_403
_can_edit_players_or_403 = can_edit_players_or_403
_can_edit_managers_or_403 = can_edit_managers_or_403
_make_team_permission_decorator = make_team_permission_decorator
_get_permissions = get_permissions
_can_manage_join_request = can_manage_join_request
_can_manage_join_request_or_403 = can_manage_join_request_or_403
