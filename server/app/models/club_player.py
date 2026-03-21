from server.app.models import db

class ClubPlayer(db.Model):
    __tablename__ = "club_player"

    club_id = db.Column(
        db.BigInteger,
        db.ForeignKey("club.id"),
        primary_key=True
    )

    player_id = db.Column(
        db.BigInteger,
        db.ForeignKey("player.id"),
        primary_key=True
    )