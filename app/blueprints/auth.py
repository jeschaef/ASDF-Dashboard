import logging

from flask import Blueprint, render_template, flash
from flask_login import login_user

from app import db
from app.auth import get_hashed_password
from app.blueprints.forms import RegisterForm, LoginForm
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


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    # If valid, create new user and redirect to
    if form.validate_on_submit():
        email = form.email.data
        name = form.username.data
        hashed_password = get_hashed_password(form.password.data)

        user = User(email=email, name=name, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        log.debug(f"Added user {user})")

        return "Success"
    # else:
    #     flash_errors(form)

    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():

        # Login user
        logged_in = login_user(form.user, form.remember_me)
        if logged_in:
            log.debug(f"Successfully logged in user {form.user})")
        else:
            log.debug(f"Could not login user {form.user})")

        return "Success"
    return render_template('auth/login.html', form=form)