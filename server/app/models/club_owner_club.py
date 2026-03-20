from server.app.models import db

class ClubOwnerClub(db.Model):
    __tablename__ = "club_owner_club"

    club_owner_id = db.Column(
        db.BigInteger,
        db.ForeignKey("club_owner.id"),
        primary_key=True
    )

    club_id = db.Column(
        db.BigInteger,
        db.ForeignKey("club.id"),
        primary_key=True
    )