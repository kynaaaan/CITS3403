import os

basedir = os.path.abspath(os.path.dirname(__file__))
default_db_loc = 'sqlite:///' + os.path.join(basedir, 'app.db')


class Config:
    SECRET_KEY = "rfp-dev-secret-key-DO-NOT-USE-IN-PRODUCTION"
    WTF_CSRF_ENABLED = True

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or default_db_loc
    SQLALCHEMY_TRACK_MODIFICATIONS = False
