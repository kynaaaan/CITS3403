from flask import Blueprint, render_template

bp = Blueprint('auth', __name__)


@bp.route('/login')
def login():
    return render_template('auth/login.html')


@bp.route('/register')
def register():
    return render_template('auth/register.html')


@bp.route('/logout')
def logout():
    # Real implementation lands with Flask-Login.
    return 'logout placeholder'
