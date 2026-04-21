from __future__ import annotations
from server.extensions import db
from server.app.models.club_owner_club import ClubOwnerClub

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from server.app.models.club import Club


class ClubOwner(db.Model):
    __tablename__ = "club_owner"

    id = db.Column(
        db.BigInteger,
        db.ForeignKey("team_manager.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    team_manager = db.relationship("TeamManager", back_populates="club_owner")

    club_associations = db.relationship(
        "ClubOwnerClub",
        back_populates="club_owner",
        cascade="all, delete-orphan",
    )

    @property
    def clubs(self) -> list[Club]:
        """Returns the list of clubs this owner manages."""
        return [a.club for a in self.club_associations]

    # ------------------------------------------------------------------
    # Permission helpers — per-club
    # ------------------------------------------------------------------

    def assoc_for(self, club: Club) -> ClubOwnerClub | None:
        """Returns the ClubOwnerClub record for the given club, or None."""
        return next(
            (a for a in self.club_associations if a.club_id == club.id),
            None,
        )

    def owns_club(self, club: Club) -> bool:
        return self.assoc_for(club) is not None

    def can_rename_club(self, club: Club) -> bool:
        a = self.assoc_for(club)
        return a is not None and a.can_rename

    def can_change_description_of(self, club: Club) -> bool:
        a = self.assoc_for(club)
        return a is not None and a.can_change_description

    def can_manage_match_in(self, club: Club) -> bool:
        a = self.assoc_for(club)
        return a is not None and a.can_manage_match

    def can_add_club_players_to(self, club: Club) -> bool:
        a = self.assoc_for(club)
        return a is not None and a.can_add_club_players

    def can_add_club_owners_to(self, club: Club) -> bool:
        a = self.assoc_for(club)
        return a is not None and a.can_add_club_owners

    def can_add_club_rule_to(self, club: Club) -> bool:
        a = self.assoc_for(club)
        return a is not None and a.can_add_club_rule

    def to_dict(self) -> dict:
        return {
            "id":      self.id,
            "clubs":   [a.to_dict() for a in self.club_associations],
        }