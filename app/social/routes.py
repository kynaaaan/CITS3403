from flask import Blueprint, render_template

bp = Blueprint('social', __name__)


@bp.route('/profile/<username>')
def profile(username):
    return render_template('social/profile.html')
