from server.extensions import db

class VenueType(db.Model):
    __tablename__ = "venue_type"
    id       = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name     = db.Column(db.String(255))
