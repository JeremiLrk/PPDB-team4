from sqlalchemy import func

from server.extensions import db


class MatchStatus(db.Model):
    __tablename__ = "match_status"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False)


class VenueType(db.Model):
    __tablename__ = "venue_type"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(32), nullable=False)


class MatchProposal(db.Model):
    __tablename__ = "match_proposal"

    id = db.Column(db.BigInteger, primary_key=True)
    proposed_by_user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sport_type_id = db.Column(
        db.BigInteger,
        db.ForeignKey("sport_type.id", ondelete="RESTRICT"),
        nullable=False,
    )
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
    )
    week_start_date = db.Column(db.Date, nullable=False)
    proposed_start_at = db.Column(db.DateTime, nullable=False)
    proposed_end_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    location = db.Column(db.String(256), nullable=True)
    venue_type_id = db.Column(
        db.BigInteger,
        db.ForeignKey("venue_type.id"),
        nullable=True,
    )

    team1 = db.relationship("Team", foreign_keys=[team1_id])
    team2 = db.relationship("Team", foreign_keys=[team2_id])
    status = db.relationship("MatchStatus")
    proposed_by = db.relationship("Account", foreign_keys=[proposed_by_user_id])
    sport_type = db.relationship("SportType")
    ruleset = db.relationship("MatchRuleSet")
    venue_type = db.relationship("VenueType")

    def to_dict(self):
        return {
            "id": self.id,
            "proposed_by_user_id": self.proposed_by_user_id,
            "sport_type_id": self.sport_type_id,
            "ruleset_id": self.ruleset_id,
            "team1_id": self.team1_id,
            "team2_id": self.team2_id,
            "status_id": self.status_id,
            "status": self.status.name if self.status else None,
            "week_start_date": self.week_start_date.isoformat() if self.week_start_date else None,
            "proposed_start_at": self.proposed_start_at.isoformat() + "Z" if self.proposed_start_at else None,
            "proposed_end_at": self.proposed_end_at.isoformat() + "Z" if self.proposed_end_at else None,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
            "location": self.location,
            "venue_type_id": self.venue_type_id,
            "team1_name": self.team1.name if self.team1 else None,
            "team2_name": self.team2.name if self.team2 else None,
        }


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


class MatchPlayed(db.Model):
    __tablename__ = "match_played"

    id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_proposal.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score_team1 = db.Column(db.Integer, nullable=False)
    score_team2 = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    played_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class MatchCancelled(db.Model):
    __tablename__ = "match_cancelled"

    id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_proposal.id", ondelete="CASCADE"),
        primary_key=True,
    )
    reason = db.Column(db.String(512), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
