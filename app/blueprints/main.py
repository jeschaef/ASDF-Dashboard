import logging

from flask import Blueprint, render_template, url_for, redirect
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
    if form.validate_on_submit():
        user = form.user
        user.password = get_hashed_password(form.new_password.data)
        db.session.commit()
        log.debug(f"Changed password: {user}")
        # TODO show some success message
        return redirect(url_for('main.profile'))

    return render_template('profile.html', form=form)


@main.route('/profile/quota')
@login_required
def quota():
    # Get datasets of the user
    owner = current_user.id
    return get_user_quota(owner)
