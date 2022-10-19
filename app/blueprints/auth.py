import datetime
import logging
import uuid

from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from flask_login import login_user, login_required, logout_user, current_user
from itsdangerous import SignatureExpired, BadSignature

from app.auth import get_hashed_password, generate_token, confirm_token
from app.blueprints.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.blueprints.util import redirect_url
from app.db import db
from app.mail import send_confirmation_mail, send_password_reset_mail
from app.model import User

auth = Blueprint('auth', __name__)
log = logging.getLogger()


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
        token = generate_token(email, current_app.config['SECRET_KEY'], current_app.config['SALT'])
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
        email = confirm_token(token, current_app.config['SECRET_KEY'], current_app.config['SALT'])
    except SignatureExpired as e:
        log.error(e)
    except BadSignature as e:
        log.error(e)

    if not email:
        pass    # TODO error occured

    # Confirm the user account
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        info_modal_title = "Account already confirmed"
        info_modal_body = "Your email address has already been confirmed."
    else:
        user.confirmed = datetime.datetime.now()
        db.session.commit()
        info_modal_title = "Confirmation successful"
        info_modal_body = "Great! Your email address was confirmed. Now you can start using the dashboard."

    return redirect(url_for('main.index', info_modal_title=info_modal_title, info_modal_body=info_modal_body))


@auth.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(redirect_url())
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm/resend')
@login_required
def resend_confirmation():
    name = current_user.name
    email = current_user.email

    # Send confirmation link via email
    token = generate_token(email, current_app.config['SECRET_KEY'], current_app.config['SALT'])
    confirmation_url = url_for('auth.confirm_email', token=token)
    send_confirmation_mail(name, email, confirmation_url)
    return redirect(redirect_url('auth.unconfirmed'))


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
    return redirect(redirect_url())


@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first_or_404()

        # Generate a token
        token = generate_token(email, current_app.config['SECRET_KEY'], current_app.config['SALT'])
        reset_url = url_for('auth.reset_password', token=token)
        send_password_reset_mail(user.name, email, reset_url)

        # Inform user about
        info_modal_title = "Password reset"
        info_modal_body = "An email with a link to reset your password has been send."
        return redirect(url_for('auth.login', info_modal_title=info_modal_title, info_modal_body=info_modal_body))

    return render_template('auth/forgot_password.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Confirm the token (might be faulty or expired)
    email = None
    try:
        email = confirm_token(token, current_app.config['SECRET_KEY'], current_app.config['SALT'])
    except SignatureExpired as e:
        log.error(e)
    except BadSignature as e:
        log.error(e)

    if not email:
        pass  # TODO error occured

    user = User.query.filter_by(email=email).first_or_404()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # update password for user
        user.password = get_hashed_password(form.password.data)
        db.session.commit()

        info_modal_title = "Password reset"
        info_modal_body = "Your password has been reset."
        return redirect(url_for('auth.login', info_modal_body=info_modal_body, info_modal_title=info_modal_title))

    return render_template('auth/reset_password.html', form=form)
