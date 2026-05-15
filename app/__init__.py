from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import Config
from utils import humanise_time

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    app.jinja_env.filters["humanise_time"] = humanise_time

    from app import models 
    from app.models import User

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
    
    @login_manager.user_loader
    def load_user(user_id):

     return User.query.get(int(user_id))

    return app
