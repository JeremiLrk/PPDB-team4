import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

config_data = {
    # Global API settings
    "app_name": "PPDB", # name of the application
    "interface": "web", # name of the current interface

    # Database settings
    "db_name": "ppdb", # name of the database
    "db_username": "ppdb_user", # The database user
    "db_password": "password", # The database password
    "db_host": "127.0.0.1", # The database host - localhost
    "db_port": 5432 # The database port
}

DEBUG = True
HOST = "127.0.0.1" if DEBUG else "0.0.0.0"
SECRET_KEY = os.getenv("SECRET_KEY", "ppdb-dev-secret-key-change-me")
