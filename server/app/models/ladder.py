from server.extensions import db


class LadderRatingFunction(db.Model):
    __tablename__ = "ladder_rating_function"

    id      = db.Column(db.BigInteger, primary_key=True)
    name    = db.Column(db.String(64), nullable=False)


class Ladder(db.Model):
    __tablename__ = "ladder"

    id          = db.Column(db.BigInteger, primary_key=True)
    club_id     = db.Column(db.BigInteger, db.ForeignKey("club.id", ondelete="CASCADE"), nullable=False)
    name        = db.Column(db.String(64),   nullable=True)
    description = db.Column(db.String(1024), nullable=True)

    sport_type_id = db.Column(
        db.BigInteger,
        db.ForeignKey("sport_type.id", ondelete="SET NULL"),
        nullable=True
    )
    ruleset_id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_rule_set.id", ondelete="SET NULL"),
        nullable=True
    )
    ladder_rating_function_id = db.Column(
        db.BigInteger,
        db.ForeignKey("ladder_rating_function.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    rule_set = db.relationship("MatchRuleSet", foreign_keys=[ruleset_id])
    ladder_rating_function = db.relationship("LadderRatingFunction", foreign_keys=[ladder_rating_function_id])
