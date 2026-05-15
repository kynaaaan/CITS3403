from flask import Blueprint
from flask import render_template

from flask_login import login_required
from flask_login import current_user

from app.models import Restaurant, Review, User

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    reviews = Review.query.order_by(Review.created_at.desc()).all()

    total_xp = User.writing_xp + User.accuracy_xp + User.explorer_xp
    top_reviewers = User.query.order_by(total_xp.desc()).limit(4).all()

    # avg_rating is a @property so sort Python side.
    # THIS WILL NEED TO BE MADE MUCH MORE EFFICIENT FOR LARGER N OF RESTAURANTS
    trending_restaurants = sorted(
        Restaurant.query.all(),
        key=lambda r: r.avg_rating,
        reverse=True,
    )[:5]

    return render_template(
        'main/index.html',
        reviews=reviews,
        top_reviewers=top_reviewers,
        trending_restaurants=trending_restaurants,
    )


@bp.route('/search')
def search():
    return render_template(
        'main/search.html',
        restaurants=Restaurant.query.all(),
    )


@bp.route('/dashboard')
@login_required
def dashboard():

    return f'Welcome {current_user.username}'