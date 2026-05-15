from flask import Blueprint, render_template, abort
from flask_login import login_required
from flask import jsonify
from flask_login import current_user
from sqlalchemy import func
from app import db
from app.models import User
from app.models import Review
from app.models import Badge
from app.gamification.logic import level_for_xp


def _find_user(username):
    """Case-insensitive username lookup so /profile/perthfoodie99 and
    /profile/PerthFoodie99 both resolve to the same user."""
    return User.query.filter(
        func.lower(User.username) == username.lower()
    ).first()

bp = Blueprint('social', __name__)

@bp.route('/profile/<username>')
def profile(username):

    user = _find_user(username)

    if not user:
        abort(404)
    
    is_owner = (
        current_user.is_authenticated 
        and current_user.id == user.id
    )
    
    is_follower = False
    if current_user.is_authenticated:
        is_follower = current_user.is_following(user)
        
    user_is_private = (
        not user.profile_is_public
        and not is_owner
        and not is_follower
    
    )
    
    reviews = []
    badges = []
    total_xp = 0
    xp_bars = []

    if not user_is_private:

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

        for label, xp, colour in [
            ('Writer',   user.writing_xp,  '#ff7e5f'),
            ('Accuracy', user.accuracy_xp, '#feb47b'),
            ('Explorer', user.explorer_xp, '#28a745'),
        ]:
            level, progress, _ = level_for_xp(xp)
            xp_bars.append({
                'label': label,
                'xp': xp,
                'colour': colour,
                'level': level,
                'progress': progress,
            })

    return render_template(
        'social/profile.html',
        user=user,
        reviews=reviews,
        badges=badges,
        total_xp=total_xp,
        xp_bars=xp_bars,
        user_is_private=user_is_private,
    )
        
@bp.route('/follow/<username>/', methods=['POST'])
@login_required
def follow(username):

    user = _find_user(username)
    if not user:
        abort(404)

    if user.id == current_user.id:

        return jsonify({
            'error': 'Cannot follow yourself'
        }), 400

    if not current_user.is_following(user):

        current_user.follow(user)

        db.session.commit()

    return jsonify({
        'following': True,
        'follower_count': user.followers.count()
    })


@bp.route('/unfollow/<username>/', methods=['POST'])
@login_required
def unfollow(username):

    user = _find_user(username)
    if not user:
        abort(404)

    if current_user.is_following(user):

        current_user.unfollow(user)

        db.session.commit()

    return jsonify({
        'following': False,
        'follower_count': user.followers.count()
    })
    