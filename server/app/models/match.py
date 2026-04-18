"""
Match models — mirrors the MATCHES section of schema.sql.

Hierarchy:
  match_proposal          — the base record (always exists)
    match_accepted        — 1-to-1 extension: proposal was accepted
    match_rejected        — 1-to-1 extension: proposal was rejected
    match_played          — 1-to-1 extension: result submitted
    match_cancelled       — 1-to-1 extension: match was cancelled (=/= rejected)

Status values (seeded into match_status):
  1 pending   — freshly proposed, awaiting response
  2 accepted  — other team accepted
  3 rejected  — other team rejected
  4 played    — result submitted
  5 cancelled — cancelled by proposing side after acceptance
"""

from __future__ import annotations
from server.extensions import db
from server.app.models.venue_type import VenueType



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
    PLAYED    = 4
    CANCELLED = 5

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


# ---------------------------------------------------------------------------
# MatchProposal  — core record
# ---------------------------------------------------------------------------

class MatchProposal(db.Model):
    __tablename__ = "match_proposal"

    id            = db.Column(db.BigInteger, primary_key=True)
    sport_type_id = db.Column(
        db.BigInteger,
        db.ForeignKey("sport_type.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_snapshot = db.Column(db.JSON, nullable=True)
    ruleset_id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_rule_set.id", ondelete="SET NULL"),
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
    location      = db.Column(db.String(256), nullable=True)
    venue_type_id = db.Column(
        db.BigInteger,
        db.ForeignKey("venue_type.id"),
        nullable=True,
    )

    # Relationships
    status     = db.relationship("MatchStatus",    back_populates="proposals")
    sport_type = db.relationship("SportType",      backref="match_proposals")
    ruleset    = db.relationship("MatchRuleSet",   backref="match_proposals")
    team1      = db.relationship("Team", foreign_keys=[team1_id], backref="home_proposals")
    team2      = db.relationship("Team", foreign_keys=[team2_id], backref="away_proposals")
    venue_type = db.relationship("VenueType",      backref="match_proposals")

    # 1-to-1 extensions
    accepted  = db.relationship("MatchAccepted",  back_populates="proposal", uselist=False, cascade="all, delete-orphan")
    rejected  = db.relationship("MatchRejected",  back_populates="proposal", uselist=False, cascade="all, delete-orphan")
    played    = db.relationship("MatchPlayed",    back_populates="proposal", uselist=False, cascade="all, delete-orphan")
    cancelled = db.relationship("MatchCancelled", back_populates="proposal", uselist=False, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "sportTypeId":  self.sport_type_id,
            "rulesetId":    self.ruleset_id,
            "team1Id":      self.team1_id,
            "team2Id":      self.team2_id,
            "status":       self.status.to_dict() if self.status else None,
            "location":     self.location,
            "venueTypeId":  self.venue_type_id,
            "ruleSnapshot": self.rule_snapshot,
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
# MatchPlayed
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
