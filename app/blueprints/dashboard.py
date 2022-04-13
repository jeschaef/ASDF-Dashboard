import logging

from flask import Blueprint, render_template
from flask_login import login_required

dashboard = Blueprint('dashboard', __name__)
log = logging.getLogger()


@dashboard.route('/dashboard')
@login_required
def index():
    return render_template('dashboard/dashboard_base.html')
