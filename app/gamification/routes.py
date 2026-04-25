from flask import Blueprint, render_template

bp = Blueprint('gamification', __name__)


@bp.route('/leaderboard')
def leaderboard():
    return render_template('gamification/leaderboard.html')
