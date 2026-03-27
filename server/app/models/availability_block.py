from server.extensions import db

class AvailabilityBlock(db.Model):
    __tablename__ = "availability_block"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("account.id", ondelete="CASCADE"), nullable=False, index=True)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)
