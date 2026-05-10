from flask_babel import Babel
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
babel = Babel()
cache = Cache()
