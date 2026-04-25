from server.extensions import db


class MatchStatus(db.Model):
    __tablename__ = "match_status"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)

    proposals = db.relationship("MatchProposal", back_populates="status")


class MatchProposal(db.Model):
    __tablename__ = "match_proposal"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sport_type_id = db.Column(db.BigInteger, db.ForeignKey("sport_type.id", ondelete="RESTRICT"), nullable=False)
    ruleset_id = db.Column(db.BigInteger, db.ForeignKey("match_rule_set.id", ondelete="SET NULL"), nullable=True)
    team1_id = db.Column(db.BigInteger, db.ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    team2_id = db.Column(db.BigInteger, db.ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    status_id = db.Column(db.BigInteger, db.ForeignKey("match_status.id", ondelete="RESTRICT"), nullable=False)
    location = db.Column(db.String(256), nullable=True)
    venue_type_id = db.Column(db.BigInteger, nullable=True)

    status = db.relationship("MatchStatus", back_populates="proposals")
    played = db.relationship("MatchPlayed", uselist=False, back_populates="proposal", cascade="all, delete-orphan")


class MatchPlayed(db.Model):
    __tablename__ = "match_played"

    id = db.Column(db.BigInteger, db.ForeignKey("match_proposal.id", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    score_team1 = db.Column(db.Integer, nullable=False)
    score_team2 = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    played_at = db.Column(db.DateTime, nullable=True)

    proposal = db.relationship("MatchProposal", back_populates="played")
