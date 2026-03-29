from server.extensions import db

class Team(db.Model):
    __tablename__ = "team"

    id = db.Column(db.BigInteger, primary_key=True)
    club_id = db.Column(db.BigInteger, nullable=True)
    name = db.Column(db.String(64), nullable=False)
    sport_type_id = db.Column(db.BigInteger)