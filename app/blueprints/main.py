import logging

from flask import Blueprint, render_template, url_for, redirect, request
from flask_login import login_required, current_user

from app.auth import get_hashed_password
from app.blueprints.forms import ChangePasswordForm
from app.blueprints.util import get_user_quota
from app.db import db

main = Blueprint('main', __name__)
log = logging.getLogger()

# a simple page that says hello & sends a mail (blocked by testing)
@main.route('/')
def index():
    # msg = Message("Hello",
    #               sender="from@example.com",
    #               recipients=["to@example.com"])
    # mail.send(msg)
    return render_template('index.html')


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ChangePasswordForm(current_user.id)
    password_updated = request.args.get("password_updated")

    if form.validate_on_submit():
        # set new password
        user = form.user
        user.password = get_hashed_password(form.new_password.data)
        db.session.commit()

        # redirect to profile page with modal for successful password update
        return redirect(url_for('main.profile', password_updated=True))

    elif form.is_submitted():
        # invalid form was submitted but if the password was updated successfully
        # directly before this, the modal would show again
        password_updated = False

    return render_template('profile.html', form=form, password_updated=password_updated)


@main.route('/profile/quota')
@login_required
def quota():
    # Get datasets of the user
    owner = current_user.id
    return get_user_quota(owner)
