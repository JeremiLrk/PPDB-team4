from server.extensions import db

class Player(db.Model):
    __tablename__ = "player"

    id = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id"),
        primary_key=True
    )