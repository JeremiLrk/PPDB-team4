from server.extensions import db

class AccountRole(db.Model):
    __tablename__ = "account_role"

    id   = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)

    accounts = db.relationship("Account", back_populates="account_role")