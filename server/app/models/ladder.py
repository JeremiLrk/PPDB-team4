from server.extensions import db


class Ladder(db.Model):
    __tablename__ = "ladder"
    id = db.Column(db.Integer, primary_key=True)

    club_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(63), nullable=True)
    description = db.Column(db.String(1023), nullable=True)
    sport_type_id = db.Column(db.Integer, nullable=True)
    ruleset_id = db.Column(db.Integer, nullable=True)


    ladder_rating_function_id = db.Column(db.Integer, nullable=False)
