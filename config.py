import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
default_db_loc = 'sqlite:///' + os.path.join(basedir, 'app.db')


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "rfp-dev-secret-key-DO-NOT-USE-IN-PRODUCTION"
    WTF_CSRF_ENABLED = True

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or default_db_loc
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
