from server.extensions import db

class AccountRole(db.Model):
    __tablename__ = "account_role"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=False)