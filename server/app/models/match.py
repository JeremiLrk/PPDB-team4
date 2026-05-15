"""
Match models — mirrors the MATCHES section of schema.sql.

Hierarchy:
  match_proposal          — the base record (always exists)
    match_accepted        — 1-to-1 extension: proposal was accepted
    match_rejected        — 1-to-1 extension: proposal was rejected
    match_played          — 1-to-1 extension: final resolved score
    match_cancelled       — 1-to-1 extension: match was cancelled (=/= rejected)

Score-submission flow (MatchScoreSubmission):
  Each played match may have up to 3 score submissions, keyed by role:
    'team1_side'   — an account authorised to manage team1's matches
    'team2_side'   — an account authorised to manage team2's matches
    'ladder_admin' — a club-owner / admin who adjudicates a disputed result;
                     only relevant when team1_side and team2_side disagree.

Status values (seeded into match_status):
  1 pending   — freshly proposed, awaiting response
  2 accepted  — other team accepted
  3 rejected  — other team rejected
  4 played    — result submitted
  5 cancelled — cancelled by proposing side after acceptance
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from server.extensions import db

if TYPE_CHECKING:
    from server.app.models.account import Account


def _contact_display_name(account: Account) -> str:
    parts = [account.first_name, account.last_name]
    name = " ".join(part.strip() for part in parts if part and part.strip())
    return name or account.email


def _serialize_contact_info(account: Account) -> dict:
    return {
        "id": account.id,
        "name": _contact_display_name(account),
        "email": account.email,
        "phoneNumber": account.phone,
    }


def _team_contact_accounts(team) -> list[Account]:
    if not team:
        return []

    accounts = []
    if getattr(team, "players", None):
        accounts.extend(
            player.account
            for player in team.players
            if getattr(player, "account", None)
        )
    if not accounts and getattr(team, "managers", None):
        accounts.extend(
            manager.account
            for manager in team.managers
            if getattr(manager, "account", None)
        )

    seen_ids: set[int] = set()
    unique_accounts = []
    for account in accounts:
        if account.id in seen_ids:
            continue
        seen_ids.add(account.id)
        unique_accounts.append(account)

    return sorted(
        unique_accounts,
        key=lambda account: (
            (account.last_name or "").lower(),
            (account.first_name or "").lower(),
            account.email.lower(),
            account.id,
        ),
    )


def _serialize_team_contacts(team) -> list[dict]:
    return [_serialize_contact_info(account) for account in _team_contact_accounts(team)]


def _team_player_accounts(team) -> list[Account]:
    if not team:
        return []

    accounts = []
    if getattr(team, "players", None):
        accounts.extend(
            player.account
            for player in team.players
            if getattr(player, "account", None)
        )

    seen_ids: set[int] = set()
    unique_accounts = []
    for account in accounts:
        if account.id in seen_ids:
            continue
        seen_ids.add(account.id)
        unique_accounts.append(account)

    return sorted(
        unique_accounts,
        key=lambda account: (
            (account.last_name or "").lower(),
            (account.first_name or "").lower(),
            account.email.lower(),
            account.id,
        ),
    )


def team_player_account_ids(team) -> set[int]:
    return {account.id for account in _team_player_accounts(team)}


def teams_share_players(team1, team2) -> bool:
    return bool(team_player_account_ids(team1) & team_player_account_ids(team2))


# ---------------------------------------------------------------------------
# Submission-role constants
# ---------------------------------------------------------------------------

class SubmissionRole(str, Enum):
    TEAM1_SIDE   = "team1_side"
    TEAM2_SIDE   = "team2_side"
    LADDER_ADMIN = "ladder_admin"


# ---------------------------------------------------------------------------
# MatchStatus  (lookup / seed table)
# ---------------------------------------------------------------------------

class MatchStatus(db.Model):
    __tablename__ = "match_status"

    id   = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    proposals = db.relationship("MatchProposal", back_populates="status")

    # Friendly constants — set after seeding
    PENDING   = 1
    ACCEPTED  = 2
    REJECTED  = 3
    CANCELLED = 4
    PLAYED    = 5

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


# ---------------------------------------------------------------------------
# MatchScoreSubmission — one row per side (up to 3 per match)
# ---------------------------------------------------------------------------

class MatchScoreSubmission(db.Model):
    __tablename__ = "match_score_submission"

    id          = db.Column(db.BigInteger, primary_key=True)
    match_id    = db.Column(
        db.BigInteger,
        db.ForeignKey("match_proposal.id", ondelete="CASCADE"),
        nullable=False,
    )
    submitted_by = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # One of SubmissionRole values; enforced by DB CHECK constraint.
    submitted_by_role = db.Column(db.String(16), nullable=False)
    score_team1  = db.Column(db.Integer, nullable=False)
    score_team2  = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # Relationships
    proposal  = db.relationship("MatchProposal", back_populates="score_submissions")
    submitter = db.relationship("Account", foreign_keys=[submitted_by])

    def scores_equal_to(self, other: MatchScoreSubmission) -> bool:
        """True when both submissions record the same score."""
        return self.score_team1 == other.score_team1 and self.score_team2 == other.score_team2

    def to_dict(self) -> dict:
        return {
            "id":              self.id,
            "matchId":         self.match_id,
            "submittedBy":     self.submitted_by,
            "submittedByRole": self.submitted_by_role,
            "scoreTeam1":      self.score_team1,
            "scoreTeam2":      self.score_team2,
            "submittedAt":     self.submitted_at.isoformat() + "Z" if self.submitted_at else None,
        }


# ---------------------------------------------------------------------------
# MatchProposal  — core record
# ---------------------------------------------------------------------------

class MatchProposal(db.Model):
    __tablename__ = "match_proposal"

    id            = db.Column(db.BigInteger, primary_key=True)
    proposed_by_user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id", ondelete="RESTRICT"),
        nullable=True,
    )
    sport_type_id = db.Column(
        db.BigInteger,
        db.ForeignKey("sport_type.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_snapshot = db.Column(db.JSON, nullable=True)
    # ruleset_id is kept for backward compatibility; it is no longer
    # authoritative — use get_ruleset() to retrieve the effective ruleset.
    ruleset_id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_rule_set.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Direct reference to the ladder this match was registered for.
    # NULL for friendly matches not belonging to any ladder.
    ladder_id = db.Column(
        db.BigInteger,
        db.ForeignKey("ladder.id", ondelete="SET NULL"),
        nullable=True,
    )
    team1_id = db.Column(
        db.BigInteger,
        db.ForeignKey("team.id", ondelete="CASCADE"),
        nullable=False,
    )
    team2_id = db.Column(
        db.BigInteger,
        db.ForeignKey("team.id", ondelete="CASCADE"),
        nullable=False,
    )
    status_id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_status.id", ondelete="RESTRICT"),
        nullable=False,
        default=MatchStatus.PENDING,
    )
    week_start_date   = db.Column(db.Date,     nullable=True)
    proposed_start_at = db.Column(db.DateTime, nullable=True)
    proposed_end_at   = db.Column(db.DateTime, nullable=True)
    created_at        = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at        = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    location          = db.Column(db.String(256), nullable=True)
    venue_type_id     = db.Column(
        db.BigInteger,
        db.ForeignKey("venue_type.id"),
        nullable=True,
    )

    # Relationships
    status      = db.relationship("MatchStatus",  back_populates="proposals")
    proposed_by = db.relationship("Account",      foreign_keys=[proposed_by_user_id])
    sport_type  = db.relationship("SportType",    backref="match_proposals")
    ruleset     = db.relationship("MatchRuleSet", backref="match_proposals")
    ladder      = db.relationship("Ladder",       foreign_keys=[ladder_id], backref="match_proposals")
    team1       = db.relationship("Team",         foreign_keys=[team1_id], backref="home_proposals")
    team2       = db.relationship("Team",         foreign_keys=[team2_id], backref="away_proposals")
    venue_type  = db.relationship("VenueType",    backref="match_proposals")

    # 1-to-1 extensions
    accepted  = db.relationship("MatchAccepted",  back_populates="proposal", uselist=False, cascade="all, delete-orphan")
    rejected  = db.relationship("MatchRejected",  back_populates="proposal", uselist=False, cascade="all, delete-orphan")
    played    = db.relationship("MatchPlayed",    back_populates="proposal", uselist=False, cascade="all, delete-orphan")
    cancelled = db.relationship("MatchCancelled", back_populates="proposal", uselist=False, cascade="all, delete-orphan")

    # Score submissions (at most 3, one per SubmissionRole)
    score_submissions = db.relationship(
        "MatchScoreSubmission",
        back_populates="proposal",
        cascade="all, delete-orphan",
        order_by="MatchScoreSubmission.submitted_at",
    )

    # ------------------------------------------------------------------
    # Ruleset helper
    # ------------------------------------------------------------------

    def get_ruleset(self):
        """Return the effective MatchRuleSet ORM object for this match.

        Priority:
          1. Ladder's current ruleset (self.ladder.rule_set) — canonical for
             ladder matches; always up to date.
          2. self.ruleset — legacy direct FK, kept for backward compatibility.

        NOTE: rule_snapshot stores a frozen JSON copy of the ruleset at
        match-creation time. Use self.rule_snapshot directly when you need
        the immutable historical record rather than the live ORM object.

        Returns None if no ruleset is linked at any level.
        """
        if self.ladder is not None and self.ladder.rule_set is not None:
            return self.ladder.rule_set
        return self.ruleset

    # ------------------------------------------------------------------
    # Score / result helpers
    # ------------------------------------------------------------------

    def _submission_for_role(self, role: SubmissionRole | str) -> MatchScoreSubmission | None:
        """Return the submission with the given role, or None."""
        role_value = role.value if isinstance(role, SubmissionRole) else role
        return next(
            (s for s in self.score_submissions if s.submitted_by_role == role_value),
            None,
        )

    @property
    def score_status(self) -> str:
        """Classify the current scoring state of this match.

        Return values
        -------------
        "not_submitted" — no score submission has been recorded yet, or only
                          one side has submitted and no dispute has been raised
        "cancelled"     — match was cancelled; score is irrelevant
        "resolved"      — match has a definitive score stored in match_played
        "disputed"      — both team sides have submitted but their scores
                          disagree; awaiting a ladder_admin adjudication
        """
        if self.cancelled:
            return "cancelled"
        if self.played:
            return "resolved"

        sub1 = self._submission_for_role(SubmissionRole.TEAM1_SIDE)
        sub2 = self._submission_for_role(SubmissionRole.TEAM2_SIDE)

        if sub1 is not None and sub2 is not None and not sub1.scores_equal_to(sub2):
            return "disputed"

        return "not_submitted"

    def get_resolved_score(self) -> dict | None:
        """Return the resolved score as ``{"scoreTeam1": int, "scoreTeam2": int}``,
        or ``None`` if no definitive result exists yet."""
        if self.played:
            return {
                "scoreTeam1": self.played.score_team1,
                "scoreTeam2": self.played.score_team2,
            }
        return None

    # ------------------------------------------------------------------
    # Permission helpers
    # ------------------------------------------------------------------

    def can_be_managed_by(self, account: Account) -> bool:
        """True if *account* is allowed to create and manage this match
        (i.e. act on behalf of at least one of the two teams).

        Qualifies when the account is:
          - an Administrator, OR
          - a ClubOwner of the club that owns team1 or team2, OR
          - a TeamManager with can_manage_match=True for team1 or team2.
        """
        from server.app.routes.matcher._permissions import _can_manage_either_team
        return _can_manage_either_team(account.resolved_role, self.team1, self.team2)

    def can_adjudicate_score(self, account: Account) -> bool:
        """True if *account* may submit the decisive 'ladder_admin' score —
        i.e. resolve a disputed result for this match.

        Qualifies when the account is:
          - an Administrator, OR
          - a ClubOwner of the club that owns the ladder this match belongs to
            (only meaningful when ladder_id is set).
        """
        from server.app.models.account import Administrator
        from server.app.models.club_owner import ClubOwner

        resolved = account.resolved_role

        if isinstance(resolved, Administrator):
            return True

        if isinstance(resolved, ClubOwner):
            owned_club_ids = {a.club_id for a in resolved.club_associations}
            match_club_ids = {
                club_id
                for club_id in (
                    self.ladder.club_id if self.ladder is not None else None,
                    self.team1.club_id if self.team1 is not None else None,
                    self.team2.club_id if self.team2 is not None else None,
                )
                if club_id is not None
            }
            return bool(owned_club_ids & match_club_ids)

        return False

    # ------------------------------------------------------------------
    # to_dict / to_dict_full
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        # Resolve the effective ruleset once (ladder ruleset takes priority
        # over the legacy direct FK, matching the logic in get_ruleset()).
        effective_ruleset = self.get_ruleset()

        return {
            "id":               self.id,
            "sportTypeId":      self.sport_type_id,
            "rulesetId":        self.ruleset_id,
            "ladderId":         self.ladder_id,
            # Human-readable names — consumed directly by the disputed-match UI
            # (DisputedMatchCard, ClubDisputedMatchesPage) without a second
            # round-trip.  Both fields are null when the match has no ladder /
            # ruleset.
            "ladderName":       self.ladder.name if self.ladder else None,
            "ruleSetName":      effective_ruleset.name if effective_ruleset else None,
            "team1Id":          self.team1_id,
            "team2Id":          self.team2_id,
            "proposedByUserId": self.proposed_by_user_id,
            "status":           self.status.to_dict() if self.status else None,
            "statusName":       self.status.name if self.status else None,
            "weekStartDate":    self.week_start_date.isoformat() if self.week_start_date else None,
            "proposedStartAt":  self.proposed_start_at.isoformat() + "Z" if self.proposed_start_at else None,
            "proposedEndAt":    self.proposed_end_at.isoformat() + "Z" if self.proposed_end_at else None,
            "createdAt":        self.created_at.isoformat() + "Z" if self.created_at else None,
            "updatedAt":        self.updated_at.isoformat() + "Z" if self.updated_at else None,
            "team1Name":        self.team1.name if self.team1 else None,
            "team2Name":        self.team2.name if self.team2 else None,
            "team1ClubId":      self.team1.club_id if self.team1 else None,
            "team2ClubId":      self.team2.club_id if self.team2 else None,
            "team1ClubCity":    self.team1.club.city if self.team1 and self.team1.club else None,
            "team2ClubCity":    self.team2.club.city if self.team2 and self.team2.club else None,
            "team1Contacts":    _serialize_team_contacts(self.team1),
            "team2Contacts":    _serialize_team_contacts(self.team2),
            "venueTypeId":      self.venue_type_id,
            "ruleSnapshot":     self.rule_snapshot,
            "scoreStatus":      self.score_status,
        }

    def to_dict_full(self) -> dict:
        """Includes nested extension data when present."""
        base = self.to_dict()
        if self.accepted:
            base["accepted"] = self.accepted.to_dict()
        if self.rejected:
            base["rejected"] = self.rejected.to_dict()
        if self.played:
            base["played"] = self.played.to_dict()
        if self.cancelled:
            base["cancelled"] = self.cancelled.to_dict()
        if self.score_submissions:
            base["scoreSubmissions"] = [s.to_dict() for s in self.score_submissions]
        return base


# ---------------------------------------------------------------------------
# MatchAccepted
# ---------------------------------------------------------------------------

class MatchAccepted(db.Model):
    __tablename__ = "match_accepted"

    id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_proposal.id", ondelete="CASCADE"),
        primary_key=True,
    )
    response_by_user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id"),
        nullable=True,
    )
    response_text = db.Column(db.String(512), nullable=True)

    proposal         = db.relationship("MatchProposal", back_populates="accepted")
    response_by_user = db.relationship("Account", foreign_keys=[response_by_user_id])

    def to_dict(self) -> dict:
        return {
            "responseByUserId": self.response_by_user_id,
            "responseText":     self.response_text,
        }


# ---------------------------------------------------------------------------
# MatchRejected
# ---------------------------------------------------------------------------

class MatchRejected(db.Model):
    __tablename__ = "match_rejected"

    id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_proposal.id", ondelete="CASCADE"),
        primary_key=True,
    )
    response_by_user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id"),
        nullable=True,
    )
    response_text = db.Column(db.String(512), nullable=True)

    proposal         = db.relationship("MatchProposal", back_populates="rejected")
    response_by_user = db.relationship("Account", foreign_keys=[response_by_user_id])

    def to_dict(self) -> dict:
        return {
            "responseByUserId": self.response_by_user_id,
            "responseText":     self.response_text,
        }


# ---------------------------------------------------------------------------
# MatchPlayed  — final resolved score (written once per match)
# ---------------------------------------------------------------------------

class MatchPlayed(db.Model):
    __tablename__ = "match_played"

    id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_proposal.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score_team1 = db.Column(db.Integer, nullable=False)
    score_team2 = db.Column(db.Integer, nullable=False)
    rating      = db.Column(db.Integer, nullable=True)
    played_at   = db.Column(db.DateTime, server_default=db.func.now())

    proposal = db.relationship("MatchProposal", back_populates="played")

    def to_dict(self) -> dict:
        return {
            "scoreTeam1": self.score_team1,
            "scoreTeam2": self.score_team2,
            "rating":     self.rating,
            "playedAt":   self.played_at.isoformat() if self.played_at else None,
        }


# ---------------------------------------------------------------------------
# MatchCancelled
# ---------------------------------------------------------------------------

class MatchCancelled(db.Model):
    __tablename__ = "match_cancelled"

    id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_proposal.id", ondelete="CASCADE"),
        primary_key=True,
    )
    reason       = db.Column(db.String(512), nullable=True)
    cancelled_at = db.Column(db.DateTime, server_default=db.func.now())

    proposal = db.relationship("MatchProposal", back_populates="cancelled")

    def to_dict(self) -> dict:
        return {
            "reason":      self.reason,
            "cancelledAt": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }


# ---------------------------------------------------------------------------
# Module-level query helpers
# ---------------------------------------------------------------------------

def get_disputed_matches() -> list[MatchProposal]:
    """Return all MatchProposal instances currently in a disputed state —
    both team sides have submitted contradicting scores and no MatchPlayed
    row exists yet.
    """
    from sqlalchemy import exists, and_

    has_t1 = exists().where(
        and_(
            MatchScoreSubmission.match_id == MatchProposal.id,
            MatchScoreSubmission.submitted_by_role == SubmissionRole.TEAM1_SIDE.value,
        )
    )
    has_t2 = exists().where(
        and_(
            MatchScoreSubmission.match_id == MatchProposal.id,
            MatchScoreSubmission.submitted_by_role == SubmissionRole.TEAM2_SIDE.value,
        )
    )
    not_resolved = ~exists().where(MatchPlayed.id == MatchProposal.id)

    candidates = (
        MatchProposal.query
        .filter(has_t1, has_t2, not_resolved)
        .all()
    )

    return [m for m in candidates if _submissions_disagree(m)]


def get_disputed_matches_resolvable_by(account: Account) -> list[MatchProposal]:
    """Return all disputed matches that *account* is authorised to adjudicate."""
    return [m for m in get_disputed_matches() if m.can_adjudicate_score(account)]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _submissions_disagree(match: MatchProposal) -> bool:
    """True when team1_side and team2_side submissions exist but differ."""
    sub1 = match._submission_for_role(SubmissionRole.TEAM1_SIDE)
    sub2 = match._submission_for_role(SubmissionRole.TEAM2_SIDE)
    if sub1 is None or sub2 is None:
        return False
    return not sub1.scores_equal_to(sub2)
