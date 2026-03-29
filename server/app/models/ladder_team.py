from server.extensions import db

class LadderTeam(db.Model):
    __tablename__ = "ladder_team"

    ladder_id = db.Column(db.BigInteger, primary_key=True)
    team_id = db.Column(db.BigInteger, primary_key=True)

    rank = db.Column(db.Integer)
    rating = db.Column(db.Integer, default=1000)
    matches_played = db.Column(db.Integer, default=0)