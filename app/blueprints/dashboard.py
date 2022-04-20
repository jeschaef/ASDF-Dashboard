import json
import logging
import os
import pandas as pd

from flask import Blueprint, render_template, current_app, url_for, request
from flask_login import login_required, current_user
from werkzeug.utils import redirect

from app import db, ensure_exists_folder
from app.blueprints.forms import UploadDatasetForm
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

    # Get all the user's datasets
    dataset_list = Dataset.query.filter_by(owner=owner)

    return render_template('dashboard/datasets.html', form=form, datasets=dataset_list)


@dashboard.route('/dashboard/datasets/delete', methods=['POST'])
@login_required
def delete_dataset():
    # Get selected datasets
    owner = current_user.id
    selected_names = json.loads(request.form.get('datasets'))
    ds = Dataset.query.filter_by(owner=owner).filter(Dataset.name.in_(selected_names)).all()

    # Remove selected datasets from database & remove data files from disk
    for d in ds:
        log.debug(f"Delete dataset {d}...")
        db.session.delete(d)
        db.session.commit()

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], owner, d.id + '.csv')
        os.remove(file_path)
        log.debug(f"Deleted dataset!")

    return redirect(url_for('dashboard.datasets'))


@dashboard.route('/dashboard/inspect', methods=['GET', 'POST'])
@login_required
def inspect():

    # Either get dataset from request via name (POST) or simply the latest uploaded (GET)
    owner = current_user.id
    selected_name = request.form.get('dataset')

    if selected_name is None:
        # Most recent uploaded
        d = Dataset.query.filter_by(owner=owner).order_by(Dataset.upload_date).first()
        # TODO no dataset uploaded
    else:
        # Get dataset from name
        d = Dataset.query.filter_by(owner=owner, name=selected_name).first()
        # TODO dataset name does not match

    # Load data
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], owner, d.id + '.csv')
    data = pd.read_csv(file_path)

    # Parses the dataframe into an HTML element with 3 Bootstrap classes assigned.
    html = data.to_html(classes=["table-bordered table-striped table-hover"])

    return render_template('dashboard/inspect.html', dataset=d, data=data, html=html)


@dashboard.route('/dashboard/evaluation')
@login_required
def evaluation():
    return render_template('dashboard/evaluation.html')
