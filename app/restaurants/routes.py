from flask import Blueprint, render_template

bp = Blueprint('restaurants', __name__)


@bp.route('/restaurant/<int:id>')
def detail(id):
    return render_template('restaurants/restaurant.html')


@bp.route('/restaurant/add')
def add():
    return render_template('restaurants/add_restaurant.html')
