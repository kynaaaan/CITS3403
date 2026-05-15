from flask import Blueprint
from flask import render_template

from flask_login import login_required
from flask_login import current_user

from app.mock_data import (
    RESTAURANTS,
    REVIEWS,
    USERS,
    enrich_review,
)

bp = Blueprint('main', __name__)


@bp.route('/')
def index():

    reviews = [enrich_review(r) for r in REVIEWS]

    top_reviewers = sorted(
        USERS,
        key=lambda u: (
            u["writing_xp"]
            + u["accuracy_xp"]
            + u["explorer_xp"]
        ),
        reverse=True,
    )[:4]

    trending_restaurants = sorted(
        RESTAURANTS,
        key=lambda r: r["avg_rating"],
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
        restaurants=RESTAURANTS,
    )


@bp.route('/dashboard')
@login_required
def dashboard():

    return f'Welcome {current_user.username}'