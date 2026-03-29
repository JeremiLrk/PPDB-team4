from server.extensions import db

class ClubOwner(db.Model):
    __tablename__ = "club_owner"

    id = db.Column(db.BigInteger, primary_key=True)