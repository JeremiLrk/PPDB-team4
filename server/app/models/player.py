from __future__ import annotations
from server.extensions import db

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from server.app.models.team import Team

class Player(db.Model):
    __tablename__ = "player"

    id = db.Column(db.BigInteger, db.ForeignKey("account.id", ondelete="CASCADE"), primary_key=True)

    # Relationship
    account = db.relationship("Account", back_populates="player")

    playerteam_associations = db.relationship("PlayerTeam", back_populates="player")
    @property
    def teams(self) -> list[Team]:
        """Returns a list of teams the player is on."""
        return [a.team for a in self.playerteam_associations]

    def to_dict(self):
        return {
            "id":      self.id,
            "teamIds": [a.team_id for a in self.playerteam_associations],
        }
class PlayerTeam(db.Model):
    __tablename__ = "player_team"

    player_id = db.Column(db.BigInteger, db.ForeignKey("player.id", ondelete="CASCADE"), primary_key=True)
    team_id = db.Column(db.BigInteger, db.ForeignKey("team.id", ondelete="CASCADE"), primary_key=True)

    # Reverse links
    player = db.relationship("Player", back_populates="playerteam_associations")
    team = db.relationship("Team", back_populates="player_associations")