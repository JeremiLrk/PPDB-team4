from server.app.models.user import db

# 1. Create the association table using the correct table name ('account.id') and type (Integer)
club_owner_club = db.Table(
    'club_owner_club',
    db.Column('club_owner_id', db.Integer, db.ForeignKey('account.id'), primary_key=True),
    db.Column('club_id', db.BigInteger, db.ForeignKey('club.id'), primary_key=True)
)

class Club(db.Model):
    __tablename__ = "club"

    id = db.Column(db.BigInteger, primary_key=True) 
    name = db.Column(db.String(64), nullable=False)

    # 2. Point the relationship to your actual 'User' class
    managers = db.relationship(
        'User', 
        secondary=club_owner_club, 
        lazy='subquery',
        backref=db.backref('managed_clubs', lazy=True)
    )