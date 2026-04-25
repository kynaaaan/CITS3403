from flask import Blueprint, render_template

bp = Blueprint('reviews', __name__)


@bp.route('/reviews/write')
def write():
    return render_template('reviews/write_review.html')
