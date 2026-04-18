from __future__ import annotations
from server.extensions import db

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from server.app.models.account import Account
    from server.app.models.club import Club


class MatchRule(db.Model):
    __tablename__ = "match_rule"

    id          = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(512), nullable=True)

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

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    is_active  = db.Column(db.Boolean, nullable=False, default=True)

    # FIX: було db.ForeignKey("account.id"), має бути match_rule.id
    replaced_by = db.Column(
        db.BigInteger,
        db.ForeignKey("match_rule.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    creator      = db.relationship("Account", foreign_keys=[creator_id])
    club         = db.relationship("Club",    foreign_keys=[club_id])
    replacement  = db.relationship("MatchRule", remote_side="MatchRule.id", foreign_keys=[replaced_by])

    rule_set_associations = db.relationship(
        "MatchRuleSetRule",
        back_populates="rule",
        cascade="all, delete-orphan",
    )

    @property
    def rule_sets(self) -> list[MatchRuleSet]:
        return [a.rule_set for a in self.rule_set_associations]

    def to_dict(self) -> dict:
        return {
            "id":                self.id,
            "name":              self.name,
            "description":       self.description,
            "canBeUsedByOthers": self.can_be_used_by_others,
            "creatorId":         self.creator_id,
            "clubId":            self.club_id,
            "createdAt":         self.created_at.isoformat() if self.created_at else None,
            "isActive":          self.is_active,
            "replacedBy":        self.replaced_by,
        }


class MatchRuleSet(db.Model):
    __tablename__ = "match_rule_set"

    id          = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(512), nullable=True)

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

    # Relationships
    creator = db.relationship("Account", foreign_keys=[creator_id])
    club    = db.relationship("Club",    foreign_keys=[club_id])

    rule_associations = db.relationship(
        "MatchRuleSetRule",
        back_populates="rule_set",
        cascade="all, delete-orphan",
    )

    @property
    def rules(self) -> list[MatchRule]:
        return [a.rule for a in self.rule_associations]

    def to_dict(self) -> dict:
        return {
            "id":                self.id,
            "name":              self.name,
            "description":       self.description,
            "canBeUsedByOthers": self.can_be_used_by_others,
            "creatorId":         self.creator_id,
            "clubId":            self.club_id,
            "ruleIds":           [a.match_rule_id for a in self.rule_associations],
        }


class MatchRuleSetRule(db.Model):
    __tablename__ = "match_rule_set_rule"

    match_rule_set_id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_rule_set.id", ondelete="CASCADE"),
        primary_key=True,
    )
    match_rule_id = db.Column(
        db.BigInteger,
        db.ForeignKey("match_rule.id", ondelete="CASCADE"),
        primary_key=True,
    )

    rule_set = db.relationship("MatchRuleSet", back_populates="rule_associations")
    rule     = db.relationship("MatchRule",    back_populates="rule_set_associations")
