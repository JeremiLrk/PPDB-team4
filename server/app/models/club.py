from server.extensions import db


club_owner_club = db.Table(
    "club_owner_club",
    db.Column("club_owner_id",
              db.BigInteger,
              db.ForeignKey("club_owner.id", ondelete="CASCADE"),
              primary_key=True),
    db.Column("club_id",
              db.BigInteger,
              db.ForeignKey("club.id", ondelete="CASCADE"),
              primary_key=True),
)

class Club(db.Model):
    __tablename__ = "club"

    id   = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    owners = db.relationship("ClubOwner", secondary=club_owner_club, back_populates="clubs")
    teams  = db.relationship("Team", back_populates="club")
