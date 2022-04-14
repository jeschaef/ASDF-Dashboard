import logging
import os

from flask import Blueprint, render_template, current_app, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename, redirect

from app import db, ensure_exists_folder
from app.blueprints.forms import UploadDatasetForm, SelectDatasetForm
from app.model import Dataset

dashboard = Blueprint('dashboard', __name__)
log = logging.getLogger()


@dashboard.route('/dashboard')
@login_required
def index():
    return render_template('dashboard/index.html')


@dashboard.route('/dashboard/datasets', methods=['GET', 'POST'])
@login_required
def datasets():
    # Upload form
    owner = current_user.id
    form = UploadDatasetForm(owner)
    if form.validate_on_submit():

        # Create dataset object from inputs
        f = form.dataset.data
        name = form.name.data
        description = form.description.data
        new_dataset = Dataset(name=name, owner=owner, description=description)

        # Add dataset object to database
        db.session.add(new_dataset)
        db.session.commit()
        log.debug(f"Added {new_dataset} to database")

        # Ensure user has an upload folder already
        user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], owner)
        ensure_exists_folder(user_folder)

        # Save data file in user_folder
        file_path = os.path.join(user_folder, new_dataset.id + '.csv')
        f.save(file_path)
        if not os.path.exists(file_path):
            db.session.delete(new_dataset)
            db.session.commit()
            # TODO report error to user
            log.debug(f"Could not save file '{file_path}'!")
        else:
            log.debug(f"Saved file '{file_path}'!")

        # Redirect to same page (to clear form inputs)
        return redirect(url_for('dashboard.datasets'))

    # Select form
    # select_form = SelectDatasetForm(owner)
    # select_form.select.choices = []
    # if select_form.validate_on_submit():
    #     log.debug(f"Validated select dataset form")
    #     d = select_form.dataset

    # Get all the user's datasets
    dataset_list = Dataset.query.filter_by(owner=owner)

    return render_template('dashboard/datasets.html', form=form, datasets=dataset_list)


@dashboard.route('/dashboard/datasets/delete', methods=['POST'])
@login_required
def delete_dataset():

    # Get selected datasets
    owner = current_user.id
    selected_names = []
    ds = Dataset.query.filter_by(owner=owner).filter(Dataset.name.in_(selected_names)).all()

    # Remove selected datasets from database & remove data files from disk
    for d in ds:
        log.debug(f"Delete dataset {d}...")
        db.session.delete(d)
        db.session.commit()

        user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], owner)
        file_path = os.path.join(user_folder, d.id + '.csv')
        os.remove(file_path)
        log.debug(f"Deleted dataset!")

    return redirect(url_for('dashboard.datasets'))



@dashboard.route('/dashboard/evaluation')
@login_required
def evaluation():
    return render_template('dashboard/evaluation.html')
