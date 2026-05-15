from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db

from app.gamification.logic import recompute_user_state
from app.models import (
    LikeDimension,
    Review,
    ReviewLike,
)
from app.reviews.forms import WriteReviewForm

bp = Blueprint('reviews', __name__)


@bp.route('/reviews/write', methods=['GET', 'POST'])
@login_required
def write():
    form = WriteReviewForm()

    # preselect restaurant from ?restaurant=<id> when linked from a restaurant page.
    if request.method == 'GET':
        try:
            preset = int(request.args.get('restaurant', 0))
            if preset > 0:
                form.restaurant_id.data = preset
        except (TypeError, ValueError):
            pass

    if form.validate_on_submit():
        review = Review(
            user_id=current_user.id,
            restaurant_id=form.restaurant_id.data,
            star_rating=form.star_rating.data,
            body=form.body.data.strip(),
            craving_tags=form.craving_tags.data,
            price_paid=form.price_paid.data,
        )
        db.session.add(review)
        db.session.flush()
        recompute_user_state(current_user)
        db.session.commit()

        flash("Review posted, nice work.", "success")
        return redirect(url_for('restaurants.detail', id=review.restaurant_id))

    return render_template('reviews/write_review.html', form=form)

@bp.route('/reviews/<int:review_id>/like/', methods=['POST'])
@login_required
def toggle_like(review_id):

    review = Review.query.get_or_404(review_id)

    data = request.get_json()

    if not data or 'dimension' not in data:

        return jsonify({
            'error': 'Missing dimension'
        }), 400

    dimension = data['dimension']

    try:
        dimension_enum = LikeDimension(dimension)

    except ValueError:

        return jsonify({
            'error': 'Invalid dimension'
        }), 400
    
    if review.user.id == current_user.id:

        return jsonify({
            'error': 'Cannot like your own review'
        }), 400

    existing_like = ReviewLike.query.filter_by(
        user_id=current_user.id,
        review_id=review.id,
        dimension=dimension_enum
    ).first()

    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        db.session.add(ReviewLike(
            user_id=current_user.id,
            review_id=review.id,
            dimension=dimension_enum,
        ))
        liked = True

    db.session.flush()
    recompute_user_state(review.user)
    db.session.commit()

    count = ReviewLike.query.filter_by(
        review_id=review.id,
        dimension=dimension_enum
    ).count()

    return jsonify({
        'liked': liked,
        'count': count
    })
    