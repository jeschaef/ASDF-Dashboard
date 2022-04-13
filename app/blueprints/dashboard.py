import logging

from flask import Blueprint, render_template
from flask_login import login_required

dashboard = Blueprint('dashboard', __name__)
log = logging.getLogger()


@dashboard.route('/dashboard')
@login_required
def index():
    return render_template('dashboard/index.html')


@dashboard.route('/dashboard/datasets')
@login_required
def datasets():
    return render_template('dashboard/datasets.html')


@dashboard.route('/dashboard/evaluation')
@login_required
def evaluation():
    return render_template('dashboard/evaluation.html')
