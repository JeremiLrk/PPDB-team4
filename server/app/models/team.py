from __future__ import annotations
from server.extensions import db

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from server.app.models.player import Player
    from server.app.models.club import Club


# ---------------------------------------------------------------------------
# TeamManagerTeam  (association table with permission columns)
# ---------------------------------------------------------------------------

class TeamManagerTeam(db.Model):
    __tablename__ = "team_manager_team"

    team_manager_id = db.Column(
        db.BigInteger,
        db.ForeignKey("team_manager.id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_id = db.Column(
        db.BigInteger,
        db.ForeignKey("team.id", ondelete="CASCADE"),
        primary_key=True,
    )

    can_rename          = db.Column(db.Boolean, nullable=False, default=True)
    can_delete          = db.Column(db.Boolean, nullable=False, default=True)
    can_edit_players    = db.Column(db.Boolean, nullable=False, default=True)
    can_edit_managers   = db.Column(db.Boolean, nullable=False, default=True)
    can_manage_match    = db.Column("can_manage_match", db.Boolean, nullable=False, default=False)

    # Reverse links
    team_manager    = db.relationship("TeamManager", back_populates="team_associations")
    team            = db.relationship("Team",        back_populates="manager_associations")

    def to_dict(self) -> dict:
        return {
            "teamId":           self.team_id,
            "canRename":        self.can_rename,
            "canDelete":        self.can_delete,
            "canEditPlayers":   self.can_edit_players,
            "canEditManagers":  self.can_edit_managers,
            "canManageMatch":   self.can_manage_match,
        }


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------

class Team(db.Model):
    __tablename__ = "team"
    __table_args__ = (
        db.UniqueConstraint("club_id", "name"),
    )

    id            = db.Column(db.BigInteger, primary_key=True)
    club_id       = db.Column(
        db.BigInteger,
        db.ForeignKey("club.id", ondelete="SET NULL"),
        nullable=True,
    )
    name          = db.Column(db.String(64), nullable=False)
    sport_type_id = db.Column(
        db.BigInteger,
        db.ForeignKey("sport_type.id", ondelete="SET NULL"),
    )

    # Relationships
    club       = db.relationship("Club",      back_populates="teams")
    sport_type = db.relationship("SportType", back_populates="teams")

    manager_associations = db.relationship(
        "TeamManagerTeam", back_populates="team", cascade="all, delete-orphan"
    )

    @property
    def managers(self) -> list[TeamManager]:
        return [a.team_manager for a in self.manager_associations]

    player_associations = db.relationship(
        "PlayerTeam", back_populates="team", cascade="all, delete-orphan"
    )

    @property
    def players(self) -> list[Player]:
        return [a.player for a in self.player_associations]

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "name":        self.name,
            "clubId":      self.club_id,
            "sportTypeId": self.sport_type_id,
        }


# ---------------------------------------------------------------------------
# TeamManager
# ---------------------------------------------------------------------------

class TeamManager(db.Model):
    __tablename__ = "team_manager"

    id = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    account    = db.relationship("Account",   back_populates="team_manager")
    club_owner = db.relationship("ClubOwner", back_populates="team_manager", uselist=False)

    team_associations = db.relationship("TeamManagerTeam", back_populates="team_manager")

    @property
    def teams(self) -> list[Team]:
        """Returns the list of teams managed by this manager."""
        return [a.team for a in self.team_associations]

    # ------------------------------------------------------------------
    # Permission helpers — per-team
    # ------------------------------------------------------------------

    def assoc_for(self, team: Team) -> TeamManagerTeam | None:
        """Returns the TeamManagerTeam record for the given team, or None."""
        return next(
            (a for a in self.team_associations if a.team_id == team.id),
            None,
        )

    def can_rename_team(self, team: Team) -> bool:
        a = self.assoc_for(team)
        return a is not None and a.can_rename

    def can_delete_team(self, team: Team) -> bool:
        a = self.assoc_for(team)
        return a is not None and a.can_delete

    def can_manage_match_in(self, club: Team) -> bool:
        a = self.assoc_for(club)
        return a is not None and a.can_manage_match

    def can_edit_players_of(self, team: Team) -> bool:
        a = self.assoc_for(team)
        return a is not None and a.can_edit_players

    def can_edit_managers_of(self, team: Team) -> bool:
        a = self.assoc_for(team)
        return a is not None and a.can_edit_managers

    def to_dict(self) -> dict:
        return {
            "id":    self.id,
            "teams": [a.to_dict() for a in self.team_associations],
        }