from __future__ import annotations
from server.extensions import db

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from server.app.models.player import Player

class TeamManager(db.Model):
    __tablename__ = "team_manager"

    id = db.Column(db.BigInteger, db.ForeignKey("account.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    account    = db.relationship("Account",   back_populates="team_manager")
    club_owner = db.relationship("ClubOwner", back_populates="team_manager", uselist=False)

    team_associations = db.relationship("TeamManagerTeam", back_populates="team_manager")
    @property
    def teams(self) -> list[Team]:
        """Returns a list of the teams managed by the manager."""
        return [a.team for a in self.team_associations]

    # Methods
    def to_dict(self):
        return {
            "id":      self.id,
            "teams":   [a.to_dict() for a in self.team_associations],
        }

class Team(db.Model):
    __tablename__ = "team"
    __table_args__ = (
      db.UniqueConstraint("club_id", "name"),
    )

    id            = db.Column(db.BigInteger, primary_key=True)
    club_id       = db.Column(db.BigInteger, db.ForeignKey("club.id", ondelete="SET NULL"), nullable=True)
    name          = db.Column(db.String(64), nullable=False)
    sport_type_id = db.Column(db.BigInteger, db.ForeignKey("sport_type.id", ondelete="SET NULL"))

    # Relationships
    club         = db.relationship("Club", back_populates="teams")
    sport_type   = db.relationship("SportType", back_populates="teams")

    manager_associations = db.relationship("TeamManagerTeam", back_populates="team")
    @property
    def managers(self) -> list[TeamManager]:
        """Returns a list of team managers."""
        return [a.team_manager for a in self.manager_associations]

    player_associations = db.relationship("PlayerTeam", back_populates="team")
    @property
    def players(self) -> list[Player]:
        """Returns a list of the team's players."""
        return [a.player for a in self.player_associations]

    # Methods
    def to_dict(self):
        """Serializes the command into a dictionary for the API response."""
        return {
            "id":          self.id,
            "name":        self.name,
            "clubId":      self.club_id,
            "sportTypeId": self.sport_type_id,
        }

class TeamManagerTeam(db.Model):
    __tablename__ = "team_manager_team"

    team_manager_id = db.Column(db.BigInteger, db.ForeignKey("team_manager.id", ondelete="CASCADE"), primary_key=True)
    team_id = db.Column(db.BigInteger, db.ForeignKey("team.id", ondelete="CASCADE"), primary_key=True)

    can_rename = db.Column(db.Boolean, nullable=False)
    can_delete = db.Column(db.Boolean, nullable=False)
    can_edit_players = db.Column(db.Boolean, nullable=False)
    can_edit_managers = db.Column(db.Boolean, nullable=False)

    # Reverse links
    team_manager = db.relationship("TeamManager", back_populates="team_associations")
    team         = db.relationship("Team",        back_populates="manager_associations")

    def to_dict(self):
        return {
            "teamId":         self.team_id,
            "canRename":      self.can_rename,
            "canDelete":      self.can_delete,
            "canEditPlayers": self.can_edit_players,
            "canEditManagers": self.can_edit_managers,
        }