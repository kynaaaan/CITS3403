from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('reviews', __name__)


@bp.route('/reviews/write')
@login_required
def write():
    return render_template('reviews/write_review.html')
