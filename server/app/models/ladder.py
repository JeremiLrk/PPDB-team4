from server.app.models import db

class Ladder(db.Model):
    __tablename__ = "ladder"
    id = db.Column(db.Integer, primary_key=True)

    club_id = db.Column(db.BigInteger, db.ForeignKey('club.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(63), nullable=True)
    description = db.Column(db.String(1023), nullable=True)
    sport_type_id = db.Column(db.Integer, nullable=True)
    ruleset_id = db.Column(db.Integer, nullable=True)


    ladder_rating_function_id = db.Column(db.Integer, nullable=False)
