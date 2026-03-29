from server.extensions import db

class Player(db.Model):
    __tablename__ = "player"

    id = db.Column(db.BigInteger, db.ForeignKey("account.id", ondelete="CASCADE"), primary_key=True)

    account = db.relationship("Account", back_populates="player")
    teams   = db.relationship("Team", secondary="player_team", back_populates="players")

    def to_dict(self):
        return self.account.to_dict()