from server.app.models import db

class ClubOwner(db.Model):
    __tablename__ = "club_owner"

    id = db.Column(db.BigInteger, primary_key=True)