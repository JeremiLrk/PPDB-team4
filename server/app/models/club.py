from server.extensions import db


class Club(db.Model):
    __tablename__ = "club"

    id          = db.Column(db.BigInteger, primary_key=True)
    name        = db.Column(db.String(64),  nullable=False)
    description = db.Column(db.String(512), nullable=True)
    sport_type_id = db.Column(
        db.BigInteger,
        db.ForeignKey("sport_type.id", ondelete="SET NULL"),
    )
    city = db.Column(db.String(128), nullable=True)
    sport_type = db.relationship("SportType")

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

    @property
    def sport_id(self):
        # Backward-compatible alias for legacy callers.
        return self.sport_type_id

    @property
    def sport(self):
        # Backward-compatible string value used by older routes/frontend.
        return self.sport_type.name if self.sport_type else None

    @sport.setter
    def sport(self, value):
        # Accept id-like values or sport name for compatibility.
        if value is None or value == "":
            self.sport_type_id = None
            return

        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            self.sport_type_id = int(value)
            return

        from server.app.models.sport_type import SportType

        match = SportType.query.filter(db.func.lower(SportType.name) == str(value).strip().lower()).first()
        self.sport_type_id = match.id if match else None

    def serialize(self) -> dict:
        """Converts the model instance to a dictionary representation."""
        return {
            "id":           self.id,
            "name":         self.name,
            "description":  self.description,
            "sport_type_id": self.sport_type_id,
            "sport_id":     self.sport_type_id,
            "sport":        self.sport,
            "city":         self.city,
        }
