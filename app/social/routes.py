from flask import Blueprint, render_template, abort

from app.mock_data import REVIEWS, enrich_review, user_by_username

bp = Blueprint('social', __name__)


@bp.route('/profile/<username>')
def profile(username):
    user = user_by_username(username)
    if not user:
        abort(404)

    # This user's reviews, pre-joined with restaurant info, most-recent first.
    # Mock data is already in chronological order (newest = lower id), so we
    # just filter and take the top 5.
    user_reviews = [
        enrich_review(r) for r in REVIEWS if r["user_id"] == user["id"]
    ][:5]

    return render_template(
        'social/profile.html',
        user=user,
        reviews=user_reviews,
        user_is_private=False,
    )
