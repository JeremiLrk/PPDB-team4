from server.app.models.user import db
from server.app.models.club_owner_club import ClubOwnerClub

class Club(db.Model):
    __tablename__ = "club"

    id = db.Column(db.BigInteger, primary_key=True) 
    name = db.Column(db.String(64), nullable=False)

    # # 2. Point the relationship to your actual 'User' class
    # managers = db.relationship(
    #     'User', 
    #     secondary=ClubOwnerClub, 
    #     lazy='subquery',
    #     backref=db.backref('managed_clubs', lazy=True)
    # )
    description = db.Column(db.String(512), nullable=False)
    sport = db.Column(db.String(64))
    city = db.Column(db.String(128))

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,  
            "description": self.description, 
            "sport": self.sport,
            "city": self.city
        }
