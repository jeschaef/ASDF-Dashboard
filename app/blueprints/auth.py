import logging
import uuid

from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user

from app import db
from app.auth import get_hashed_password
from app.blueprints.forms import RegisterForm, LoginForm
from app.blueprints.util import redirect_url
from app.model import User

auth = Blueprint('auth', __name__)
log = logging.getLogger()


def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')


def perform_login(user, remember=False):
    # Create & store new session token
    user.session_token = uuid.uuid4().hex
    db.session.commit()

    # Login
    logged_in = login_user(user, remember)
    if logged_in:
        log.debug(f"Successfully logged in user {user} (remember_me={remember})")
    else:
        log.debug(f"Could not login user {user})")


@auth.route('/register', methods=['GET', 'POST'])
def register():
    # if already logged in, redirect to main page
    if current_user.is_authenticated:
        return redirect(redirect_url())

    # Register form: validate, create new user (+login) and redirect
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        name = form.username.data
        hashed_password = get_hashed_password(form.password.data)

        user = User(email=email, name=name, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        log.debug(f"Added user {user})")
        perform_login(user)

        return redirect(redirect_url())

    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # if already logged in, redirect to main page
    if current_user.is_authenticated:
        return redirect(redirect_url())

    # Login form: validate, login via login_mngr and redirect
    form = LoginForm()
    if form.validate_on_submit():
        perform_login(form.user, form.remember_me.data)
        return redirect(redirect_url())

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    log.debug(f"Logged out user successfully")
    return redirect(url_for('main.index'))
