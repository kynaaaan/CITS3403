from flask import Blueprint
from flask import render_template
from flask import request

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
    suburb  = request.args.get('suburb', '').strip()
    cuisine = request.args.get('cuisine', '').strip()
    price   = request.args.get('price', '').strip()

    q = Restaurant.query
    if suburb:
        q = q.filter(Restaurant.suburb == suburb)
    if price:
        try:
            q = q.filter(Restaurant.price_range == int(price))
        except ValueError:
            pass  # ignore garbage values

    restaurants = q.order_by(Restaurant.name).all()
    if cuisine:
        restaurants = [r for r in restaurants if cuisine in (r.cuisine_tags or [])]

    return render_template(
        'main/search.html',
        restaurants=restaurants,
        selected_suburb=suburb,
        selected_cuisine=cuisine,
        selected_price=price,
    )


