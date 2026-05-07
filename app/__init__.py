from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

# Defined at module scope so blueprints / models / scripts can import them.
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so Alembic sees them in db.metadata when generating
    # migrations. Must come after db.init_app.
    from app import models  # noqa: F401

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

    @app.context_processor
    def inject_display_mappings():
        from app.mock_data import SUBURB_DISPLAY, CUISINE_DISPLAY, PRICE_DISPLAY
        return {
            "SUBURB_DISPLAY": SUBURB_DISPLAY,
            "CUISINE_DISPLAY": CUISINE_DISPLAY,
            "PRICE_DISPLAY": PRICE_DISPLAY,
        }

    return app
