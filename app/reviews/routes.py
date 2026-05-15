from flask import Blueprint, render_template
from flask import jsonify
from flask import request
from flask_login import login_required
from flask_login import current_user

from app import db

from app.models import (
    Review,
    ReviewLike,
    LikeDimension,
)

bp = Blueprint('reviews', __name__)


@bp.route('/reviews/write')
def write():
    return render_template('reviews/write_review.html')

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

        new_like = ReviewLike(
            user_id=current_user.id,
            review_id=review.id,
            dimension=dimension_enum
        )

        db.session.add(new_like)

        liked = True
        
        if dimension_enum == LikeDimension.ACCURACY:
            review.user.accuracy_xp += 5
        elif dimension_enum == LikeDimension.WRITING:
            review.user.writing_xp +=5
        elif dimension_enum == LikeDimension.BREADTH:
            review.user.explorer_xp += 5

    db.session.commit()

    count = ReviewLike.query.filter_by(
        review_id=review.id,
        dimension=dimension_enum
    ).count()

    return jsonify({
        'liked': liked,
        'count': count
    })
    