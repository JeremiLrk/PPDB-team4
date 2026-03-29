from server.app.models import db

# Voeg deze klassen toe zodat SQLAlchemy de relaties begrijpt
class SportType(db.Model):
    __tablename__ = "sport_type"
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

class MatchRuleSet(db.Model):
    __tablename__ = "match_rule_set"
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

class LadderRatingFunction(db.Model):
    __tablename__ = "ladder_rating_function"
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

class Ladder(db.Model):
    __tablename__ = "ladder"
    id = db.Column(db.BigInteger, primary_key=True)
    club_id = db.Column(db.BigInteger, db.ForeignKey('club.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(1024), nullable=True)
    
    # Gebruik de ForeignKeys naar de nieuwe modellen
    sport_type_id = db.Column(db.BigInteger, db.ForeignKey('sport_type.id'), nullable=True)
    ruleset_id = db.Column(db.BigInteger, db.ForeignKey('match_rule_set.id'), nullable=True)
    ladder_rating_function_id = db.Column(db.BigInteger, db.ForeignKey('ladder_rating_function.id'), nullable=False, default=1)