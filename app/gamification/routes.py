from flask import Blueprint, render_template
from sqlalchemy import func
from app.gamification.badges import BADGES
from app import db
from app.models import User
from app.models import Review
from app.models import Restaurant

bp = Blueprint('gamification', __name__)

@bp.route('/leaderboard')
def leaderboard():

    top_users = db.session.query(
        User.username,

        (
            User.writing_xp
            + User.accuracy_xp
            + User.explorer_xp
        ).label('total_xp')

    ).order_by(

        (
            User.writing_xp
            + User.accuracy_xp
            + User.explorer_xp
        ).desc()

    ).limit(10).all()

    suburb_reviews = db.session.query(

        Restaurant.suburb,
        func.count(Review.id)

    ).join(

        Review,
        Review.restaurant_id == Restaurant.id

    ).group_by(
        
        Restaurant.suburb
        
    ).all()

    prolific_explorer = db.session.query(

        User.username,
        User.explorer_xp

    ).order_by(

        User.explorer_xp.desc()

    ).first()
    
    top_user_labels = [
        user.username for user in top_users
    ]

    top_user_xp = [
        user.total_xp for user in top_users
    ]
    suburb_labels = [ 
        suburb[0] for suburb in suburb_reviews
    ]
    suburb_counts = [ 
        suburb[1] for suburb in suburb_reviews
    ]

    return render_template(
        'gamification/leaderboard.html',

        top_users=top_users,
        suburb_reviews=suburb_reviews,
        prolific_explorer=prolific_explorer,
        top_user_labels=top_user_labels,
        top_user_xp=top_user_xp,
        suburb_labels=suburb_labels,
        suburb_counts=suburb_counts,
    )
    
@bp.route('/badges')
def badges():

    return render_template(
        'gamification/badges.html',

        badges=BADGES
    )       
