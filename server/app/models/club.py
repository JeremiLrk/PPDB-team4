from server.app.models.user import db


class Club(db.Model):
    __tablename__ = "club"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
