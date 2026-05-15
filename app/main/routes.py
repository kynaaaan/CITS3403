from flask import Blueprint, render_template, request
from flask_login import current_user
from sqlalchemy import String, cast

from app.mock_data import CUISINE_DISPLAY, SUBURB_DISPLAY
from app.models import Follow, Restaurant, Review, User

bp = Blueprint('main', __name__)


LATEST_REVIEWS_LIMIT = 20
VALID_FEEDS = {'global', 'following', 'suburb', 'cuisine'}


@bp.route('/')
def index():
    feed = request.args.get('feed', 'global').strip().lower()
    if feed not in VALID_FEEDS:
        feed = 'global'

    suburb = request.args.get('suburb', '').strip().lower()
    if suburb and suburb not in SUBURB_DISPLAY:
        suburb = ''

    cuisine = request.args.get('cuisine', '').strip().lower()
    if cuisine and cuisine not in CUISINE_DISPLAY:
        cuisine = ''

    needs_login = (feed == 'following' and not current_user.is_authenticated)

    reviews = []
    if not needs_login:
        q = Review.query.order_by(Review.created_at.desc())

        if feed == 'following':
            # ids of everyone current_user follows.
            followed_ids = (
                Follow.query
                .with_entities(Follow.followed_id)
                .filter(Follow.follower_id == current_user.id)
            )
            q = q.filter(Review.user_id.in_(followed_ids))

        elif feed == 'suburb' and suburb:
            q = q.join(Review.restaurant).filter(Restaurant.suburb == suburb)

        elif feed == 'cuisine' and cuisine:
            q = q.join(Review.restaurant).filter(
                cast(Restaurant.cuisine_tags, String).like(f'%"{cuisine}"%')
            )

        reviews = q.limit(LATEST_REVIEWS_LIMIT).all()

    total_xp = User.writing_xp + User.accuracy_xp + User.explorer_xp
    top_reviewers = User.query.order_by(total_xp.desc()).limit(4).all()

    trending_restaurants = sorted(
        Restaurant.query.all(),
        key=lambda r: r.avg_rating,
        reverse=True,
    )[:5]

    return render_template(
        'main/index.html',
        reviews=reviews,
        active_feed=feed,
        selected_suburb=suburb,
        selected_cuisine=cuisine,
        needs_login=needs_login,
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
