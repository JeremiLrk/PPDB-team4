"""
match_score_service.py
======================
Business logic for the score-submission flow.

Submission lifecycle
--------------------
1. A manager/owner/player on team1 submits a score  → role 'team1_side'
2. A manager/owner/player on team2 submits a score  → role 'team2_side'
3a. Both scores agree → finalize_match() is called automatically,
    MatchPlayed is written, status becomes PLAYED.
3b. Scores disagree  -> match enters 'disputed' state.
4. A ladder admin (ClubOwner of the ladder's club, or Administrator)
   submits the decisive score -> role 'ladder_admin'
5. finalize_match() is called with the admin's score,
   MatchPlayed is written, status becomes PLAYED.

MatchPlayed semantics
---------------------
MatchPlayed is the authoritative, immutable record of the final result.
It is NEVER written directly by a submitting account; it is always
produced by finalize_match() once the result is unambiguous.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from server.app.models.match import (
    MatchPlayed,
    MatchProposal,
    MatchScoreSubmission,
    MatchStatus,
    SubmissionRole,
    _submissions_disagree,
)
from server.app.services.elo_service import apply_elo_for_match_result
from server.extensions import db

if TYPE_CHECKING:
    from server.app.models.account import Account


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ScoreSubmissionError(Exception):
    """Raised when a submission cannot be recorded."""
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


def submit_score(
    proposal: MatchProposal,
    account: Account,
    score_team1: int,
    score_team2: int,
) -> tuple[MatchScoreSubmission, bool]:
    """Record a score submission from *account* for *proposal*.

    Determines the correct SubmissionRole for *account*, persists the
    MatchScoreSubmission row, then checks whether the match can be
    immediately finalized.

    Returns
    -------
    (submission, finalized)
        submission  — the MatchScoreSubmission that was just written
        finalized   — True if finalize_match() was called automatically
                      (i.e. both sides agreed or admin adjudicated)

    Raises
    ------
    ScoreSubmissionError
        - proposal is already finalized / cancelled
        - account has no valid role for this match
        - account's role already has a submission
        - 'ladder_admin' submission attempted when scores are not disputed
        - scores contain negative values
    """
    _validate_scores(score_team1, score_team2)
    _guard_already_finalized(proposal)

    role = _resolve_role(proposal, account)

    existing = proposal._submission_for_role(role)
    if existing is not None:
        raise ScoreSubmissionError(
            f"A score from '{role.value}' side was already submitted for this match.",
            status_code=409,
        )

    if role == SubmissionRole.LADDER_ADMIN and not _submissions_disagree(proposal):
        raise ScoreSubmissionError(
            "Ladder-admin adjudication is only allowed when team sides disagree.",
            status_code=409,
        )

    submission = MatchScoreSubmission(
        match_id=proposal.id,
        submitted_by=account.id,
        submitted_by_role=role.value,
        score_team1=score_team1,
        score_team2=score_team2,
    )
    db.session.add(submission)
    db.session.flush()  # populate submission.id; keep transaction open

    # Reload the relationship so _submission_for_role sees the new row
    db.session.refresh(proposal)

    finalized = _try_finalize(proposal)
    return submission, finalized


def finalize_match(proposal: MatchProposal, score_team1: int, score_team2: int) -> MatchPlayed:
    """Write the authoritative MatchPlayed record and set status to PLAYED.

    Should only be called when the result is unambiguous (both sides
    agreed, or a ladder_admin submission exists).  submit_score() calls
    this automatically; direct callers should have a compelling reason.

    Raises
    ------
    ScoreSubmissionError  if the match is already finalized or cancelled.
    """
    _guard_already_finalized(proposal)

    played = MatchPlayed(
        id=proposal.id,
        score_team1=score_team1,
        score_team2=score_team2,
    )
    db.session.add(played)

    played_status = db.session.get(MatchStatus, MatchStatus.PLAYED)
    proposal.status_id = played_status.id
    proposal.updated_at = datetime.now(timezone.utc)

    apply_elo_for_match_result(
        team1_id=proposal.team1_id,
        team2_id=proposal.team2_id,
        score_team1=score_team1,
        score_team2=score_team2,
    )

    return played


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_scores(score_team1: int, score_team2: int) -> None:
    if score_team1 < 0 or score_team2 < 0:
        raise ScoreSubmissionError("Scores must be >= 0.")


def _guard_already_finalized(proposal: MatchProposal) -> None:
    if proposal.cancelled:
        raise ScoreSubmissionError("Cannot submit a score for a cancelled match.", status_code=409)
    if proposal.played:
        raise ScoreSubmissionError("This match has already been finalized.", status_code=409)


def _resolve_role(proposal: MatchProposal, account: Account) -> SubmissionRole:
    """Determine which SubmissionRole *account* fills for *proposal*.

    Priority: ladder_admin > team1_side > team2_side.
    Raises ScoreSubmissionError if account has no valid role.
    """
    from server.app.routes.matcher._permissions import _can_manage_match

    resolved = account.resolved_role

    # ladder_admin takes priority over team-side roles (see docstring).
    # The submit_score guard enforces that ladder_admin submissions are only
    # accepted when scores are actually disputed.
    if proposal.can_adjudicate_score(account):
        return SubmissionRole.LADDER_ADMIN

    # team1_side / team2_side
    if _can_score_for_team(account, proposal.team1, resolved=resolved):
        return SubmissionRole.TEAM1_SIDE
    if _can_score_for_team(account, proposal.team2, resolved=resolved):
        return SubmissionRole.TEAM2_SIDE

    raise ScoreSubmissionError(
        "Forbidden: you are not authorised to submit a score for this match.",
        status_code=403,
    )


def _can_score_for_team(account: Account, team, *, resolved=None) -> bool:
    """True when the account may submit the score for *team*.

    Team scores can be submitted by the usual managers/owners as well as by
    players who are actually on the team.
    """
    from server.app.routes.matcher._permissions import _can_manage_match

    if resolved is None:
        resolved = account.resolved_role

    if _can_manage_match(resolved, team):
        return True

    return account.player is not None and team in account.player.teams


def _try_finalize(proposal: MatchProposal) -> bool:
    """Finalize the match if the result is now unambiguous.

    Returns True if finalize_match() was called.
    """
    admin_sub = proposal._submission_for_role(SubmissionRole.LADDER_ADMIN)
    if admin_sub is not None:
        # Admin adjudication is always decisive
        finalize_match(proposal, admin_sub.score_team1, admin_sub.score_team2)
        return True

    sub1 = proposal._submission_for_role(SubmissionRole.TEAM1_SIDE)
    sub2 = proposal._submission_for_role(SubmissionRole.TEAM2_SIDE)

    if sub1 is not None and sub2 is not None and sub1.scores_equal_to(sub2):
        # Both sides agree
        finalize_match(proposal, sub1.score_team1, sub1.score_team2)
        return True

    return False
