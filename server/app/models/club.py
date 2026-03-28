from server.app.models.user import db

# 1. Create the association table for the Many-to-Many relationship
club_owner_club = db.Table(
    'club_owner_club',
    db.Column('club_owner_id', db.BigInteger, db.ForeignKey('club_owner.id'), primary_key=True),
    db.Column('club_id', db.BigInteger, db.ForeignKey('club.id'), primary_key=True)
)

class Club(db.Model):
    __tablename__ = "club"

    id = db.Column(db.BigInteger, primary_key=True) # Changed to BigInteger to match your SQL!
    name = db.Column(db.String(64), nullable=False)

    # 2. Add the relationship so we can easily check managers
    managers = db.relationship(
        'ClubOwner', # Change this if your model is called 'User'
        secondary=club_owner_club, 
        lazy='subquery',
        backref=db.backref('managed_clubs', lazy=True)
    )