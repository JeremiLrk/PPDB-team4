from server.app.models.user import db


class Club(db.Model):
    __tablename__ = "club"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(512), nullable=False)
    sport = db.Column(db.String(64))
    city = db.Column(db.String(128))

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,  
            "description": self.description, 
            "sport": self.sport,
            "city": self.city
        }