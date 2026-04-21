from server.extensions import db


class Club(db.Model):
    __tablename__ = "club"

    id          = db.Column(db.BigInteger, primary_key=True)
    name        = db.Column(db.String(64),  nullable=False)
    description = db.Column(db.String(512), nullable=False)
    sport_type_id = db.Column(
        db.BigInteger,
        db.ForeignKey("sport_type.id", ondelete="SET NULL"),
    )
    city = db.Column(db.String(128), nullable=False)

    # Relationships
    owner_associations = db.relationship(
        "ClubOwnerClub",
        back_populates="club",
        cascade="all, delete-orphan",
    )

    @property
    def owners(self):
        return [a.club_owner for a in self.owner_associations]

    teams = db.relationship("Team", back_populates="club")

    def serialize(self) -> dict:
        return {
            "id":           self.id,
            "name":         self.name,
            "description":  self.description,
            "sport_id":     self.sport_id,
            "city":         self.city,
        }
