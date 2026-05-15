from flask import Blueprint, render_template
from sqlalchemy import func

from app.models import User

bp = Blueprint('social', __name__)


@bp.route('/profile/<username>')
def profile(username):
    user = User.query.filter(
        func.lower(User.username) == username.lower()
    ).first_or_404()

    user_reviews = sorted(user.reviews, key=lambda r: r.created_at, reverse=True)[:5]

    return render_template(
        'social/profile.html',
        user=user,
        reviews=user_reviews,
        user_is_private=False,
    )
