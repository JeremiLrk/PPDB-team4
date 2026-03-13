from server.app import create_app
from server.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Dropping all tables including dependencies...")
    db.session.execute(text("DROP SCHEMA public CASCADE"))
    db.session.execute(text("CREATE SCHEMA public"))
    db.session.execute(text("GRANT ALL ON SCHEMA public TO public"))  # restore rights
    db.session.commit()
    print("Database schema reset complete.")