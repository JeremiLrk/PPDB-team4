from server.extensions import db
from server.app.models.club_owner_club import ClubOwnerClub

class Club(db.Model):
    __tablename__ = "club"

    id = db.Column(db.BigInteger, primary_key=True) 
    name = db.Column(db.String(64), nullable=False)

    # # 2. Point the relationship to your actual 'Account' class
    # managers = db.relationship(
    #     'Account', 
    #     secondary=ClubOwnerClub, 
    #     lazy='subquery',
    #     backref=db.backref('managed_clubs', lazy=True)
    # )
    description = db.Column(db.String(512), nullable=False)
    sport_type_id = db.Column(db.Integer, nullable=True)
    city = db.Column(db.String(128))
    owners = db.relationship("ClubOwner", secondary=ClubOwnerClub.__tablename__, back_populates="clubs")
    teams  = db.relationship("Team", back_populates="club")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,  
            "description": self.description, 
            "sport_type_id": self.sport_type_id,
            "city": self.city
        }
