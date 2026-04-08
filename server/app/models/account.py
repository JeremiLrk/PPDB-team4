from server.extensions import db


class AccountRole(db.Model):
    __tablename__ = "account_role"

    id   = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)

    accounts = db.relationship("Account", back_populates="account_role")

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
    player        = db.relationship("Player", back_populates="account", uselist=False)
    team_manager  = db.relationship("TeamManager", back_populates="account", uselist=False)

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

    @property
    def resolved_roles(self) -> list:
        """Returns all active roles for this account."""
        roles = []
        if self.administrator:
            roles.append(self.administrator)
        if self.team_manager and self.team_manager.club_owner:
            roles.append(self.team_manager.club_owner)
        elif self.team_manager:
            roles.append(self.team_manager)
        if self.player:
            roles.append(self.player)
        return roles

    def to_dict(self, include=None):
        """
        include: list of additional data to include.
        Possible values: "player", "team_manager", "club_owner", "administrator"
        If None — returns basic information.
        """

        roles = []
        if self.administrator:
            roles.append("administrator")
        if self.team_manager and self.team_manager.club_owner:
            roles.append("club_owner")
        elif self.team_manager:
            roles.append("team_manager")
        if self.player:
            roles.append("player")
        if not roles:
            roles.append("user")


        managed_team_ids = []
        if self.team_manager:
            managed_team_ids = [t.id for t in self.team_manager.teams]

        club_ids = []
        if self.team_manager and self.team_manager.club_owner:
            club_ids = [c.id for c in self.team_manager.club_owner.clubs]

        base = {
            "id":               self.id,
            "email":            self.email,
            "firstName":        self.first_name,
            "lastName":         self.last_name,
            "roles":            roles,
            "managedTeamIds":   managed_team_ids,
            "clubIds":          club_ids,
        }

        if include:
            include = set(include)
            if "player" in include and self.player:
                base["player"] = self.player.to_dict()
            if "team_manager" in include and self.team_manager:
                base["teamManager"] = self.team_manager.to_dict()
            if "club_owner" in include and self.team_manager and self.team_manager.club_owner:
                base["clubOwner"] = self.team_manager.club_owner.to_dict()
            if "administrator" in include and self.administrator:
                base["administrator"] = self.administrator.to_dict()

        return base

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
