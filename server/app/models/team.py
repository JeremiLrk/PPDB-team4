from server.extensions import db

player_team = db.Table(
    "player_team",
    db.Column("player_id",
                db.BigInteger,
                db.ForeignKey("player.id", ondelete="CASCADE"),
                primary_key=True),
    db.Column("team_id",
              db.BigInteger,
              db.ForeignKey("team.id", ondelete="CASCADE"),
              primary_key=True),
)

team_manager_team = db.Table(
    "team_manager_team",
    db.Column("team_manager_id",
              db.BigInteger,
              db.ForeignKey("team_manager.id", ondelete="CASCADE"),
              primary_key=True),
    db.Column("team_id",
              db.BigInteger,
              db.ForeignKey("team.id", ondelete="CASCADE"),
              primary_key=True
              ),
)

class Team(db.Model):
    __tablename__ = "team"
    __table_args__ = (
      db.UniqueConstraint("club_id", "name"),
    )

    id            = db.Column(db.BigInteger, primary_key=True)
    club_id       = db.Column(db.BigInteger, db.ForeignKey("club.id", ondelete="SET NULL"), nullable=True)
    name          = db.Column(db.String(64), nullable=False)
    sport_type_id = db.Column(db.BigInteger, db.ForeignKey("sport_type.id", ondelete="SET NULL"))

    # Relationships
    club         = db.relationship("Club", back_populates="teams")
    sport_type   = db.relationship("SportType", back_populates="teams")
    players      = db.relationship("Player", secondary=player_team, back_populates="teams")
    managers     = db.relationship("TeamManager", secondary=team_manager_team, back_populates="teams")

    def to_dict(self):
      return {
        "id":          self.id,
        "name":        self.name,
        "clubId":      self.club_id,
        "sportTypeId": self.sport_type_id,
      }