from server.extensions import db 
from server.app.models.account_role import AccountRole

class User(db.Model):
    __tablename__ = "account"
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)

    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="user")
    
    account_role_id = db.Column(db.Integer, db.ForeignKey('account_role.id'), nullable=False, default=1)