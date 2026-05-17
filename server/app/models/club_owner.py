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
        if hasattr(self, "_clubs_override"):
            return self._clubs_override
        return [a.club for a in self.club_associations]

    @clubs.setter
    def clubs(self, value: list[Club]) -> None:
        # Backward-compatible in-memory assignment for tests/helpers that do
        # not materialize ClubOwnerClub association objects.
        self._clubs_override = value

    # ------------------------------------------------------------------
    # Permission helpers — per-club
    # ------------------------------------------------------------------

    def assoc_for(self, club: Club) -> ClubOwnerClub | None:
        """Returns the ClubOwnerClub record for the given club, or None."""
        return next(
            (a for a in self.club_associations if a.club_id == club.id),
            None,
        )

    """Convenience methods for checking permissions on a per-club basis."""
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
        """Converts the model instance to a dictionary representation."""
        return {
            "id":      self.id,
            "clubs":   [a.to_dict() for a in self.club_associations],
        }
