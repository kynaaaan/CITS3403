from flask import Blueprint, flash, redirect, render_template, abort, url_for
from flask_login import current_user, login_required

from app import db
from app.mock_data import REVIEWS, enrich_review, restaurant_by_id
from app.models import Restaurant
from app.restaurants.forms import AddRestaurantForm

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


@bp.route('/restaurant/add', methods=['GET', 'POST'])
@login_required
def add():
    form = AddRestaurantForm()

    if form.validate_on_submit():
        restaurant = Restaurant(
            name=form.name.data.strip(),
            suburb=form.suburb.data,
            cuisine_tags=form.cuisine_tags.data,   # list of slug strings
            price_range=int(form.price_range.data),
            created_by=current_user.id,
        )
        db.session.add(restaurant)
        db.session.commit()

        flash(f'"{restaurant.name}" has been added — now write the first review!', 'success')
        return redirect(url_for('restaurants.detail', id=restaurant.id))

    return render_template('restaurants/add_restaurant.html', form=form)