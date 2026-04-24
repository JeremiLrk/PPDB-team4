from server.extensions import db
from server.app.models.club_owner import ClubOwner
from server.app.models.player import Player

class Account(db.Model):
    __tablename__ = "account"

    id            = db.Column(db.BigInteger, primary_key=True)
    first_name    = db.Column(db.String(32))
    last_name     = db.Column(db.String(32))
    date_of_birth = db.Column(db.Date)
    email         = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    account_role_id = db.Column(db.BigInteger, db.ForeignKey("account_role.id", ondelete="CASCADE"), nullable=False)

    account_role  = db.relationship("AccountRole", back_populates="accounts")
    administrator = db.relationship("Administrator", back_populates="account", uselist=False)
    player        = db.relationship("Player",        back_populates="account", uselist=False)
    team_manager  = db.relationship("TeamManager",   back_populates="account", uselist=False)

    is_verified = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def resolved_role(self):
        """Returns the model with the highest level of inheritance."""
        if self.team_manager and self.team_manager.club_owner:
            return self.team_manager.club_owner
        if self.team_manager:
            return self.team_manager
        if self.administrator:
            return self.administrator
        if self.player:
            return self.player
        return self

    def to_dict(self):
        resolved = self.resolved_role

        if isinstance(resolved, Administrator):
            role = "administrator"
        elif isinstance(resolved, ClubOwner):
            role = "club_owner"
        elif isinstance(resolved, TeamManager):
            role = "team_manager"
        elif isinstance(resolved, Player):
            role = "player"
        else:
            role = "user"

        # IDs of teams the account manages (as TeamManager or ClubOwner)
        managed_team_ids = []
        if self.team_manager:
            managed_team_ids = [t.id for t in self.team_manager.teams]

        # IDs of clubs the account owns (only for ClubOwner)
        club_ids = []
        if isinstance(resolved, ClubOwner):
            club_ids = [c.id for c in resolved.clubs]

        return {
            "id":             self.id,
            "email":          self.email,
            "firstName":      self.first_name,
            "lastName":       self.last_name,
            "role":           role,
            "managedTeamIds": managed_team_ids,
            "clubIds":        club_ids,
        }

class Administrator(db.Model):
    __tablename__ = "administrator"
    __table_args__ = (
        db.CheckConstraint("access_level >= 0", name="chk_positive_access_level"),
    )

    id           = db.Column(db.BigInteger, db.ForeignKey("account.id", ondelete="CASCADE"), primary_key=True)
    access_level = db.Column(db.Integer, nullable=False)

    account = db.relationship("Account", back_populates="administrator")

    def to_dict(self):
        return {
            "id":          self.id,
            "accessLevel": self.access_level,
        }


# Backward-compatible re-exports for modules/tests importing these from account.
from server.app.models.team import TeamManager  # noqa: E402
from server.app.models.club_owner import ClubOwner  # noqa: E402
