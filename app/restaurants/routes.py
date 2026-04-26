from flask import Blueprint, render_template, abort

from app.mock_data import REVIEWS, enrich_review, restaurant_by_id

bp = Blueprint('restaurants', __name__)


@bp.route('/restaurant/<int:id>')
def detail(id):
    restaurant = restaurant_by_id(id)
    if not restaurant:
        abort(404)

    # Reviews for this restaurant, pre-joined with their author.
    reviews = [enrich_review(r) for r in REVIEWS if r["restaurant_id"] == id]

    # Star distribution for the sidebar rating-breakdown bars.
    # distribution[0] = number of 1-star reviews, ..., distribution[4] = 5-stars.
    distribution = [0, 0, 0, 0, 0]
    for r in reviews:
        distribution[r["star_rating"] - 1] += 1

    return render_template(
        'restaurants/restaurant.html',
        restaurant=restaurant,
        reviews=reviews,
        rating_distribution=distribution,
    )


@bp.route('/restaurant/add')
def add():
    return render_template('restaurants/add_restaurant.html')
