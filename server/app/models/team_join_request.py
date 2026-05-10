from server.extensions import db


class TeamJoinRequest(db.Model):
    __tablename__ = "team_join_request"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    team_id = db.Column(
        db.BigInteger,
        db.ForeignKey("team.id"),
        nullable=False,
    )

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id"),
        nullable=False,
    )

    date = db.Column(
        db.DateTime,
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending",
    )

    team = db.relationship("Team")
    account = db.relationship("Account")

    def serialize(self):
        return {
            "id": self.id,
            "team_id": self.team_id,
            "user_id": self.user_id,
            "team_name": self.team.name,
            "requested_at": self.date,
            "status": self.status,
        }
