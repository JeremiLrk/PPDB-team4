from __future__ import annotations
from server.extensions import db

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from server.app.models.club import Club
    from server.app.models.club_owner import ClubOwner


class ClubOwnerClub(db.Model):
    __tablename__ = "club_owner_club"

    club_owner_id = db.Column(
        db.BigInteger,
        db.ForeignKey("club_owner.id", ondelete="CASCADE"),
        primary_key=True,
    )
    club_id = db.Column(
        db.BigInteger,
        db.ForeignKey("club.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Permissions (mirrors the SQL DDL exactly)
    can_rename             = db.Column(db.Boolean, nullable=False, default=False)
    can_change_description = db.Column(db.Boolean, nullable=False, default=False)
    can_manage_match       = db.Column("can_manage_match", db.Boolean, nullable=False, default=False)
    can_add_club_players   = db.Column(db.Boolean, nullable=False, default=False)
    can_add_club_owners    = db.Column(db.Boolean, nullable=False, default=False)
    can_add_club_rule      = db.Column(db.Boolean, nullable=False, default=False)

    # Reverse links
    club_owner = db.relationship("ClubOwner", back_populates="club_associations")
    club       = db.relationship("Club",      back_populates="owner_associations")

    def to_dict(self) -> dict:
        return {
            "clubId":               self.club_id,
            "canRename":            self.can_rename,
            "canChangeDescription": self.can_change_description,
            "canManageMatch":       self.can_manage_match,
            "canAddClubPlayers":    self.can_add_club_players,
            "canAddClubOwners":     self.can_add_club_owners,
            "canAddClubRule":       self.can_add_club_rule,
        }
