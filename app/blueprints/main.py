import logging

from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_required, current_user

from app.auth import get_hashed_password
from app.blueprints.util import data_size
from app.db import db
from app.blueprints.forms import ChangePasswordForm
from app.model import Dataset

main = Blueprint('main', __name__)
log = logging.getLogger()

MAX_QUOTA = 10 * 1024 * 1024       # 10 mb

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
        form = ChangePasswordForm(current_user.id)
        return redirect(url_for('main.profile'))

        # TODO show some success message
    return render_template('profile.html', form=form)


@main.route('/profile/quota')
@login_required
def quota():
    # Get datasets of the user
    owner = current_user.id
    all_datasets = Dataset.query.filter_by(owner=owner).all()   # TODO no datasets uploaded yet
    quota_used = {}
    bytes_used = 0
    for d in all_datasets:
        size = data_size(owner, d.id)
        quota_used[d.name] = size
        bytes_used += size
    bytes_free = MAX_QUOTA - bytes_used
    return {'quota_used': quota_used, 'quota_free': bytes_free}
