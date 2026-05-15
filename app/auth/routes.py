from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash

from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required

from app import db
from app.models import User

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(
            username=username
        ).first()

        if user and user.check_password(password):

            login_user(user)

            return redirect(
                url_for('main.index')
            )

        flash('Invalid username or password')

    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:

            flash('Username already exists')

            return redirect(
                url_for('auth.register')
            )

        user = User(
            username=username,
            email=email,
        )

        user.set_password(password)

        db.session.add(user)

        db.session.commit()

        flash('Account created successfully')

        return redirect(
            url_for('auth.login')
        )

    return render_template('auth/register.html')


@bp.route('/logout')
@login_required
def logout():

    logout_user()

    return redirect(
        url_for('main.index')
    )