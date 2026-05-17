from __future__ import annotations
from server.extensions import db

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from server.app.models.account import Account
    from server.app.models.club import Club

VALID_MATCH_FORMATS    = {"best_of_3", "timed", "pro_set"}
VALID_THIRD_SET_FORMATS = {"full_set", "super_tiebreak"}
VALID_DEUCE_RULES      = {"advantage", "golden_point"}
VALID_GAME_FORMATS     = {"singles", "doubles"}


class MatchRuleSet(db.Model):
    __tablename__ = "match_rule_set"

    id          = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(64),  nullable=False)
    description = db.Column(db.String(512), nullable=True)

    match_format           = db.Column(db.String(20), nullable=False, default="best_of_3")
    timed_duration_minutes = db.Column(db.Integer,    nullable=True)
    pro_set_games          = db.Column(db.Integer,    nullable=True)
    third_set_format       = db.Column(db.String(20), nullable=False, default="super_tiebreak")
    deuce_rule             = db.Column(db.String(20), nullable=False, default="advantage")
    game_format            = db.Column(db.String(20), nullable=False, default="doubles")

    can_be_used_by_others = db.Column(db.Boolean, nullable=False, default=True)

    creator_id = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id", ondelete="SET NULL"),
        nullable=True,
    )
    club_id = db.Column(
        db.BigInteger,
        db.ForeignKey("club.id", ondelete="SET NULL"),
        nullable=True,
    )

    creator = db.relationship("Account", foreign_keys=[creator_id])
    club    = db.relationship("Club",    foreign_keys=[club_id])

    def to_dict(self) -> dict:
        """Converts the model instance to a dictionary representation."""
        return {
            "id":                   self.id,
            "name":                 self.name,
            "description":          self.description,
            "matchFormat":          self.match_format,
            "timedDurationMinutes": self.timed_duration_minutes,
            "proSetGames":          self.pro_set_games,
            "thirdSetFormat":       self.third_set_format,
            "deuceRule":            self.deuce_rule,
            "gameFormat":           self.game_format,
            "canBeUsedByOthers":    self.can_be_used_by_others,
            "creatorId":            self.creator_id,
            "clubId":               self.club_id,
        }
