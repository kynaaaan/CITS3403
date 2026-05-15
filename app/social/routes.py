from flask import Blueprint, render_template, abort
from flask_login import login_required
from flask import jsonify
from flask_login import current_user
from app import db
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
        
    return render_template(
        'social/profile.html',
        user=user,
        reviews=reviews,
        badges=badges,
        total_xp=total_xp,
        user_is_private=user_is_private,
    )
        
@bp.route('/follow/<username>/', methods=['POST'])
@login_required
def follow(username):

    user = User.query.filter_by(
        username=username
    ).first_or_404()

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

    user = User.query.filter_by(
        username=username
    ).first_or_404()

    if current_user.is_following(user):

        current_user.unfollow(user)

        db.session.commit()

    return jsonify({
        'following': False,
        'follower_count': user.followers.count()
    })
    