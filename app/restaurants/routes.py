from collections import Counter

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Restaurant
from app.restaurants.forms import AddRestaurantForm, EditRestaurantForm

bp = Blueprint('restaurants', __name__)


@bp.route('/restaurant/<int:id>')
def detail(id):
    restaurant = Restaurant.query.get_or_404(id)
    reviews = sorted(restaurant.reviews, key=lambda r: r.created_at, reverse=True)

    # Star distribution for the sidebar rating-breakdown bars.
    # distribution[0] = number of 1-star reviews, ..., distribution[4] = 5-stars.
    distribution = [0, 0, 0, 0, 0]
    for r in reviews:
        distribution[r.star_rating - 1] += 1

    # CRAVING COUNTS
    craving_counter = Counter()
    for r in reviews:
        craving_counter.update(r.craving_tags or [])
    top_cravings = craving_counter.most_common(5)

    # FOLLOWED AUTHORS COUNT
    followed_authors = []
    if current_user.is_authenticated:
        followed_ids = {f.followed_id for f in current_user.following}
        seen = set()
        for r in reviews:
            if r.user_id in followed_ids and r.user_id not in seen:
                followed_authors.append(r.user)
                seen.add(r.user_id)
                if len(followed_authors) >= 3:
                    break

    # SPARKLINE DATA
    chronological = list(reversed(reviews))
    sparkline_labels = [r.created_at.strftime('%b %d') for r in chronological]
    sparkline_data = [r.star_rating for r in chronological]

    return render_template(
        'restaurants/restaurant.html',
        restaurant=restaurant,
        reviews=reviews,
        rating_distribution=distribution,
        top_cravings=top_cravings,
        followed_authors=followed_authors,
        sparkline_labels=sparkline_labels,
        sparkline_data=sparkline_data,
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


@bp.route('/restaurant/manage')
@login_required
def manage_redirect():
    # Resolver shortcut for restaurant accounts: send them straight to their owned page.
    if not current_user.is_restaurant_account:
        abort(403)

    owned = Restaurant.query.filter_by(owner_id=current_user.id).first()
    if owned:
        return redirect(url_for('restaurants.detail', id=owned.id))

    flash("You haven't claimed a restaurant yet, find your listing and claim it.", 'info')
    return redirect(url_for('main.search'))


@bp.route('/restaurant/<int:id>/claim', methods=['POST'])
@login_required
def claim(id):
    # Only restaurant accounts can claim, and a page can only be claimed once.
    # Auto-approved for MVP, no admin verification step YET.
    if not current_user.is_restaurant_account:
        abort(403)

    restaurant = Restaurant.query.get_or_404(id)

    if restaurant.owner_id is not None:
        flash('This restaurant has already been claimed.', 'warning')
        return redirect(url_for('restaurants.detail', id=id))

    # one owned restaurant per account.
    already_owns = Restaurant.query.filter_by(owner_id=current_user.id).first()
    if already_owns:
        flash('Restaurant accounts can manage one page at a time.', 'warning')
        return redirect(url_for('restaurants.detail', id=already_owns.id))

    restaurant.owner_id = current_user.id
    db.session.commit()
    flash(f'You now manage {restaurant.name}.', 'success')
    return redirect(url_for('restaurants.detail', id=id))


@bp.route('/restaurant/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    restaurant = Restaurant.query.get_or_404(id)
    if current_user.id != restaurant.owner_id:
        abort(403)

    form = EditRestaurantForm(
        restaurant_id=restaurant.id,
        data={
            'name': restaurant.name,
            'suburb': restaurant.suburb,
            'cuisine_tags': restaurant.cuisine_tags,
            'price_range': str(restaurant.price_range),
        },
    )

    if form.validate_on_submit():
        restaurant.name = form.name.data.strip()
        restaurant.suburb = form.suburb.data
        restaurant.cuisine_tags = form.cuisine_tags.data
        restaurant.price_range = int(form.price_range.data)
        db.session.commit()
        flash('Restaurant details updated.', 'success')
        return redirect(url_for('restaurants.detail', id=restaurant.id))

    return render_template(
        'restaurants/edit_restaurant.html',
        form=form,
        restaurant=restaurant,
    )