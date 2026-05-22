from server.extensions import db

class SportType(db.Model):
  __tablename__ = "sport_type"
  id       = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
  name     = db.Column(db.String(255), nullable=False, unique=True)
  minimum_number_of_players_on_a_team      = db.Column(db.Integer)
  maximum_number_of_players_per_team = db.Column(db.Integer)

  teams = db.relationship("Team", back_populates="sport_type")
