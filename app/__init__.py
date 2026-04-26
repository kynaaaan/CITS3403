from flask import Flask

from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

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
            "PRICE_DISPLAY": PRICE_DISPLAY
        }

    return app
