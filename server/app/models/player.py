from server.extensions import db


class PlayerTeam(db.Model):
    __tablename__ = "player_team"

    player_id = db.Column(
        db.BigInteger,
        db.ForeignKey("player.id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_id = db.Column(
        db.BigInteger,
        db.ForeignKey("team.id", ondelete="CASCADE"),
        primary_key=True,
    )

    player = db.relationship("Player", back_populates="playerteam_associations")
    team = db.relationship("Team", back_populates="player_associations")


class Player(db.Model):
    __tablename__ = "player"

    id = db.Column(db.BigInteger, db.ForeignKey("account.id", ondelete="CASCADE"), primary_key=True)

    account = db.relationship("Account", back_populates="player")
    playerteam_associations = db.relationship(
        "PlayerTeam",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    @property
    def teams(self):
        return [a.team for a in self.playerteam_associations]

    def to_dict(self):
        return self.account.to_dict()
