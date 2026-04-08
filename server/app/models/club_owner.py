from server.app.models.club_owner_club import ClubOwnerClub
from server.extensions import db

class ClubOwner(db.Model):
    __tablename__ = "club_owner"

    id = db.Column(db.BigInteger, db.ForeignKey("team_manager.id", ondelete="CASCADE"), primary_key=True)

    team_manager = db.relationship("TeamManager", back_populates="club_owner")
    clubs        = db.relationship("Club", secondary=ClubOwnerClub.__tablename__, back_populates="owners")

    def to_dict(self):
        return self.account.to_dict()