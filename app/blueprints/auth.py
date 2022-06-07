import datetime
import logging
import uuid

from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from flask_login import login_user, login_required, logout_user, current_user
from itsdangerous import SignatureExpired, BadSignature

from app.db import db
from app.auth import get_hashed_password, generate_confirmation_token, confirm_token
from app.blueprints.forms import RegisterForm, LoginForm
from app.blueprints.util import redirect_url
from app.mail import mail, send_confirmation_mail
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

    # Register form: validate, create new user and redirect
    form = RegisterForm()
    if form.validate_on_submit():

        # Get form data
        email = form.email.data
        name = form.username.data
        hashed_password = get_hashed_password(form.password.data)

        # Create and add user
        user = User(email=email, name=name, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        log.debug(f"Added {user} to database")

        # Send confirmation link via email
        token = generate_confirmation_token(email, current_app.config['SECRET_KEY'], current_app.config['SALT'])
        confirmation_url = url_for('auth.confirm_email', token=token, _external=True)
        send_confirmation_mail(name, email, confirmation_url)

        # Login user & redirect
        perform_login(user)
        return redirect(redirect_url('auth.unconfirmed'))

    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm_email(token):
    # Confirm the token (might be faulty or expired)
    email = None
    try:
        email = confirm_token(token)
    except SignatureExpired as e:
        log.error(e)
    except BadSignature as e:
        log.error(e)

    if not email:
        pass    # TODO error occured

    # Confirm the user account
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed.', 'success')      # TODO
    else:
        user.confirmed = datetime.datetime.now()
        db.session.commit()
    return redirect(url_for('main.index'))


@auth.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect('main.index')
    return render_template('auth/unconfirmed.html')


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
