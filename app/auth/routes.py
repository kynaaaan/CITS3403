from urllib.parse import urlsplit

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from app import db
from app.auth.forms import LoginForm, RegisterForm
from app.models import User

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)

        # Safe-redirect: only allow relative URLs back to our own app.
        next_url = request.args.get('next')
        if not next_url or urlsplit(next_url).netloc != '':
            next_url = url_for('main.index')

        return redirect(next_url)

    return render_template('auth/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegisterForm()

    if form.validate_on_submit():

        user = User(
            username=form.username.data,
            email=form.email.data,
            is_restaurant_account=form.is_restaurant_account.data,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Account created — please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
