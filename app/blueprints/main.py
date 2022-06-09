import logging

from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_required, current_user

from app.auth import get_hashed_password
from app.blueprints.forms import ChangePasswordForm, PasswordConfirmationForm
from app.blueprints.util import get_user_quota, delete_all_datasets, delete_user_account
from app.db import db

main = Blueprint('main', __name__)
log = logging.getLogger()


# a simple page that says hello & sends a mail (blocked by testing)
@main.route('/')
def index():
    return render_template('index.html')


@main.route('/test')
def test():
    return render_template('mail/confirmation.html')


@main.route('/profile')
@login_required
def profile():
    form = ChangePasswordForm(current_user.id)
    con_form_dataset = PasswordConfirmationForm(current_user.id, 'password_dataset')
    con_form_account = PasswordConfirmationForm(current_user.id, 'password_account')
    return render_template('profile.html', form=form, con_form_dataset=con_form_dataset,
                           con_form_account=con_form_account)


@main.route('/profile/change_password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm(current_user.id)
    con_form_dataset = PasswordConfirmationForm(current_user.id, 'password_dataset', was_submitted=False)
    con_form_account = PasswordConfirmationForm(current_user.id, 'password_account', was_submitted=False)

    if form.validate_on_submit():
        # set new password
        user = form.user
        user.password = get_hashed_password(form.new_password.data)
        db.session.commit()

        # redirect to profile page with modal for successful password update
        return redirect(url_for('main.profile', info_modal_title="Password changed",
                                info_modal_body="Your password has successfully been updated!"))

    return render_template('profile.html', form=form, con_form_dataset=con_form_dataset,
                           con_form_account=con_form_account)


@main.route('/profile/delete_datasets', methods=['POST'])
@login_required
def delete_datasets():
    form = ChangePasswordForm(current_user.id, was_submitted=False)
    con_form_dataset = PasswordConfirmationForm(current_user.id, 'password_dataset')
    con_form_account = PasswordConfirmationForm(current_user.id, 'password_account', was_submitted=False)

    # Delete all datasets password confirmation
    if con_form_dataset.validate_on_submit():
        delete_all_datasets(current_user.id)
        return redirect(url_for('main.profile', info_modal_title="Deleted All Datasets",
                                info_modal_body="Your datasets were deleted."))

    return render_template('profile.html', form=form, con_form_dataset=con_form_dataset,
                           con_form_account=con_form_account)


@main.route('/profile/delete_account', methods=['POST'])
@login_required
def delete_account():
    form = ChangePasswordForm(current_user.id, was_submitted=False)
    con_form_dataset = PasswordConfirmationForm(current_user.id, 'password_dataset', was_submitted=False)
    con_form_account = PasswordConfirmationForm(current_user.id, 'password_account')

    # Delete account password confirmation
    if con_form_account.validate_on_submit():
        delete_user_account(current_user)
        return redirect(url_for('main.index', info_modal_title="Account deleted",
                                info_modal_body="Your account has been deleted."))

    return render_template('profile.html', form=form, con_form_dataset=con_form_dataset,
                           con_form_account=con_form_account)


@main.route('/profile/quota')
@login_required
def quota():
    # Get datasets of the user
    owner = current_user.id
    return get_user_quota(owner)
