from flask import Blueprint, render_template, abort

from app.models import User
from app.models import Review
from app.models import Badge

bp = Blueprint('social', __name__)


@bp.route('/profile/<username>')
def profile(username):

    user = User.query.filter_by(
        username=username
    ).first()

    if not user:
        abort(404)

    reviews = Review.query.filter_by(
        user_id=user.id
    ).order_by(
        Review.created_at.desc()
    ).limit(5).all()

    badges = Badge.query.filter_by(
        user_id=user.id
    ).all()

    total_xp = (
        user.writing_xp
        + user.accuracy_xp
        + user.explorer_xp
    )

    return render_template(
        'social/profile.html',
        user=user,
        reviews=reviews,
        badges=badges,
        total_xp=total_xp,
        user_is_private=False,
    )