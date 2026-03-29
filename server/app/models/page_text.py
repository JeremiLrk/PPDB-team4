from server.extensions import db

class PageText(db.Model):
    __tablename__ = "page_text"
    id       = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    page     = db.Column(db.String(50))
    key      = db.Column(db.String(100))
    language = db.Column(db.String(5))
    value    = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint("page", "key", "language"),
    )