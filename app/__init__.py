import os

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import Config, ProductionConfig
from utils import humanise_time

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to continue.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'


def create_app(config_class=None):
    if config_class is None:
        config_class = (
            ProductionConfig
            if os.environ.get('FLASK_CONFIG') == 'production'
            else Config
        )

    app = Flask(__name__)
    app.config.from_object(config_class)
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.jinja_env.filters["humanise_time"] = humanise_time

    from app import models 

    from app.auth.routes import bp as auth_bp
    from app.main.routes import bp as main_bp
    from app.restaurants.routes import bp as restaurants_bp
    from app.reviews.routes import bp as reviews_bp
    from app.social.routes import bp as social_bp
    from app.gamification.routes import bp as gamification_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(restaurants_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(gamification_bp)

    from app.seed import seed_command
    app.cli.add_command(seed_command)

    @app.context_processor
    def inject_display_mappings():
        from app.mock_data import SUBURB_DISPLAY, CUISINE_DISPLAY, PRICE_DISPLAY
        return {
            "SUBURB_DISPLAY": SUBURB_DISPLAY,
            "CUISINE_DISPLAY": CUISINE_DISPLAY,
            "PRICE_DISPLAY": PRICE_DISPLAY,
        }

    return app
