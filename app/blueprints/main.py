import logging

from flask import Blueprint, render_template, url_for, redirect, request
from flask_login import login_required, current_user

from app.auth import get_hashed_password
from app.blueprints.forms import ChangePasswordForm
from app.blueprints.util import get_user_quota, delete_data
from app.db import db
from app.model import Dataset, User

main = Blueprint('main', __name__)
log = logging.getLogger()

# a simple page that says hello & sends a mail (blocked by testing)
@main.route('/')
def index():
    return render_template('index.html')


@main.route('/test')
def test():
    return render_template('mail/confirmation.html')


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


@main.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    owner = current_user.id

    # Delete user datasets first
    all_datasets = Dataset.query.filter_by(owner=owner).all()
    for d in all_datasets:
        delete_data(owner, d)

    # Delete user upload folder

    # Delete user account
    user = User.query.get(owner)
    db.session.delete(user)
    db.session.commit()
    log.debug(f"Deleted user {user}")

    return redirect(url_for('auth.logout'))

