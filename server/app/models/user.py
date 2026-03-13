from server.extensions import db


class User(db.Model):
    __tablename__ = "account"
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)

    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
<<<<<<< HEAD
=======

   # admin_profile = db.relationship("Administrator", backref="account", uselist=False)
"""
def is_admin(self):
        return self.admin_profile is not None
    
class Administrator(db.Model):
    __tablename__ = "administrator"
    
    # References the account id
    id = db.Column(db.BigInteger, db.ForeignKey('account.id'), primary_key=True)
    access_level = db.Column(db.Integer, nullable=False, default=0)
    # Additional fields for administrators can be added here

# 1. Create the base User account
new_admin_user = User(
    first_name="PPDB",
    last_name="4",
    email="ppdb4@example.com",
    password_hash="test4ppdb",
    id=1 # Assuming 1 is the ID for 'Admin' in your account_role table
)

# 2. Create the Administrator profile and link it
admin_profile = Administrator(access_level=10)
new_admin_user.admin_profile = admin_profile

# 3. Save both to the DB
def seed_admin(app):
    with app.app_context():
        # Check if user exists first to avoid duplicates
        db.session.add(new_admin_user)
        db.session.commit()

db.session.commit()"""
>>>>>>> e275562 (beetje vanalles)
