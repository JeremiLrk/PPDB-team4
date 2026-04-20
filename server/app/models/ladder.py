from server.extensions import db

# 1. Association Table: Links MatchRuleSets and Rules together
match_ruleset_rules = db.Table('match_ruleset_rules',
                               db.Column('match_ruleset_id', db.BigInteger, db.ForeignKey('match_rule_set.id'), primary_key=True),
                               db.Column('rule_id', db.BigInteger, db.ForeignKey('rule.id'), primary_key=True)
                               )

# 2. The Rule Model (Individual strings)
class Rule(db.Model):
    __tablename__ = 'rule'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    content = db.Column(db.String(255), nullable=False, unique=True)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content
        }

# 3. Your Existing MatchRuleSet (Upgraded)
class MatchRuleSet(db.Model):
    __tablename__ = "match_rule_set"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(512), nullable=True)

    # The Many-to-Many Relationship to Rules
    rules = db.relationship('Rule', secondary=match_ruleset_rules, lazy='subquery',
                            backref=db.backref('match_rulesets', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rules": [rule.to_dict() for rule in self.rules]
        }

# 4. Your Existing LadderRatingFunction
class LadderRatingFunction(db.Model):
    __tablename__ = "ladder_rating_function"
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

# 5. Your Existing Ladder (Updated with ForeignKey)
class Ladder(db.Model):
    __tablename__ = "ladder"
    id = db.Column(db.Integer, primary_key=True)

    club_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(63), nullable=True)
    description = db.Column(db.String(1023), nullable=True)
    sport_type_id = db.Column(db.Integer, nullable=True)

    # Updated to BigInteger to match MatchRuleSet, and added the ForeignKey
    ruleset_id = db.Column(db.BigInteger, db.ForeignKey('match_rule_set.id'), nullable=True)

    # A relationship helper so you can easily access ladder.ruleset in your code
    ruleset = db.relationship('MatchRuleSet', backref='ladders')

    ladder_rating_function_id = db.Column(db.Integer, nullable=False)