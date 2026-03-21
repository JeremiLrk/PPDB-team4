from server.app.models import db

class ClubJoinRequest(db.Model):
    __tablename__ = "club_join_request"

    club_id = db.Column(
        db.BigInteger,
        db.ForeignKey("club.id"),
        primary_key=True
    )

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id"),
        primary_key=True
    )

    date = db.Column(
        db.DateTime,
        nullable=False
    )

    club = db.relationship("Club") 

    def serialize(self):
        return {
            "club_id": self.club_id,
            "user_id": self.user_id,
            "club_name": self.club.name,  
            "requested_at": self.date, 
            "status": "pending"  
        }