from server.app.models.sport_type import SportType
from server.extensions import db


class TeamClubJoinRequest(db.Model):
    __tablename__ = "team_club_join_request"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    club_id = db.Column(
        db.BigInteger,
        db.ForeignKey("club.id", ondelete="CASCADE"),
        nullable=False,
    )

    team_id = db.Column(
        db.BigInteger,
        db.ForeignKey("team.id", ondelete="CASCADE"),
        nullable=False,
    )

    ladder_id = db.Column(
        db.BigInteger,
        db.ForeignKey("ladder.id", ondelete="SET NULL"),
        nullable=True,
    )

    requested_by = db.Column(
        db.BigInteger,
        db.ForeignKey("account.id", ondelete="SET NULL"),
        nullable=True,
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

    club = db.relationship("Club")
    team = db.relationship("Team")
    ladder = db.relationship("Ladder")
    requester = db.relationship("Account")

    def serialize(self):
        ladder_sport = db.session.get(SportType, self.ladder.sport_type_id) if self.ladder and self.ladder.sport_type_id else None
        return {
            "id": self.id,
            "club_id": self.club_id,
            "clubId": self.club_id,
            "club_name": self.club.name if self.club else None,
            "clubName": self.club.name if self.club else None,
            "team_id": self.team_id,
            "teamId": self.team_id,
            "team_name": self.team.name if self.team else None,
            "teamName": self.team.name if self.team else None,
            "ladder_id": self.ladder_id,
            "ladderId": self.ladder_id,
            "ladder_name": self.ladder.name if self.ladder else None,
            "ladderName": self.ladder.name if self.ladder else None,
            "ladder_sport_id": self.ladder.sport_type_id if self.ladder else None,
            "ladderSportId": self.ladder.sport_type_id if self.ladder else None,
            "ladder_sport_name": ladder_sport.name if ladder_sport else None,
            "ladderSportName": ladder_sport.name if ladder_sport else None,
            "requested_by": self.requested_by,
            "requestedBy": self.requested_by,
            "requested_at": self.date.isoformat() if self.date else None,
            "requestedAt": self.date.isoformat() if self.date else None,
            "sport_name": self.team.sport_type.name if self.team and self.team.sport_type else None,
            "sportName": self.team.sport_type.name if self.team and self.team.sport_type else None,
            "sport_mismatch": bool(
                self.ladder
                and self.team
                and self.ladder.sport_type_id
                and self.team.sport_type_id
                and self.ladder.sport_type_id != self.team.sport_type_id
            ),
            "sportMismatch": bool(
                self.ladder
                and self.team
                and self.ladder.sport_type_id
                and self.team.sport_type_id
                and self.ladder.sport_type_id != self.team.sport_type_id
            ),
            "status": self.status,
            "type": "team_club_invitation",
        }
