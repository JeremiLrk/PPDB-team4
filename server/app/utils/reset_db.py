from server.app.models.user import db
from server.app import create_app
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Dropping all tables including dependencies...")
    db.session.execute(text("DROP SCHEMA public CASCADE"))
    db.session.execute(text("CREATE SCHEMA public"))
    db.session.commit()
    print("Database schema reset complete.")