"""
configs:

    Config           dev defaults; SECRET_KEY and DATABASE_URL fall back
                     to safe local values so the team can boot the app
                     without writing a .env first.
    ProductionConfig no defaults; refuses to start if SECRET_KEY or
                     DATABASE_URL are missing. Secure cookies on.

create_app() picks ProductionConfig iff FLASK_CONFIG=production.
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = (
        os.environ.get('SECRET_KEY')
        or 'rfp-dev-secret-key-DO-NOT-USE-IN-PRODUCTION'
    )
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL')
        or 'sqlite:///' + os.path.join(basedir, 'app.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    @classmethod
    def init_app(cls, app):
        missing = [k for k in ('SECRET_KEY', 'DATABASE_URL') if not os.environ.get(k)]
        if missing:
            raise RuntimeError(
                f"Production requires env vars: {', '.join(missing)}"
            )
