from flask import Blueprint, abort, flash, jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import func


from app import db
from app.gamification.badges import badge_cards_for
from app.gamification.logic import level_for_xp
from app.models import Badge, Review, User
from app.social.forms import ProfileEditForm


def _find_user(username):
    """Case-insensitive username lookup"""
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
    badge_cards = []
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
        badge_cards = badge_cards_for(badges)

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

    follower_count = len(user.followers)
    following_count = len(user.following)

    return render_template(
        'social/profile.html',
        user=user,
        reviews=reviews,
        badges=badges,
        badge_cards=badge_cards,
        total_xp=total_xp,
        xp_bars=xp_bars,
        user_is_private=user_is_private,
        is_owner=is_owner,
        is_follower=is_follower,
        follower_count=follower_count,
        following_count=following_count,
    )
        
@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """
    Account management page for the logged-in user.
    """
    form = ProfileEditForm()

    if form.validate_on_submit():
        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip().lower()
        current_user.profile_is_public = form.profile_is_public.data

        if form.new_password.data:
            current_user.set_password(form.new_password.data)

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('social.dashboard'))

    if not form.is_submitted():
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.profile_is_public.data = current_user.profile_is_public

    # view model
    reviews = current_user.reviews
    suburbs_visited = len({r.restaurant.suburb for r in reviews})
    cuisines_reviewed = len({
        tag for r in reviews for tag in (r.restaurant.cuisine_tags or [])
    })
    likes_received = sum(len(r.likes) for r in reviews)

    total_xp = (
        current_user.writing_xp
        + current_user.accuracy_xp
        + current_user.explorer_xp
    )
    combined_level, combined_progress, xp_to_next = level_for_xp(total_xp)

    xp_bars = []
    for label, xp, colour in [
        ('Writer',   current_user.writing_xp,  '#ff7e5f'),
        ('Accuracy', current_user.accuracy_xp, '#feb47b'),
        ('Explorer', current_user.explorer_xp, '#28a745'),
    ]:
        level, progress, _ = level_for_xp(xp)
        xp_bars.append({
            'label': label,
            'xp': xp,
            'colour': colour,
            'level': level,
            'progress': progress,
        })

    badge_cards = badge_cards_for(current_user.badges)

    return render_template(
        'social/dashboard.html',
        form=form,
        review_count=len(reviews),
        suburbs_visited=suburbs_visited,
        cuisines_reviewed=cuisines_reviewed,
        likes_received=likes_received,
        total_xp=total_xp,
        combined_level=combined_level,
        combined_progress=combined_progress,
        xp_to_next=xp_to_next,
        xp_bars=xp_bars,
        badge_cards=badge_cards,
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
        'follower_count': len(user.followers),
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
        'follower_count': len(user.followers),
    })
