import logging

from flask import Blueprint, render_template

dashboard = Blueprint('dashboard', __name__)
log = logging.getLogger()


@dashboard.route('/dashboard')
def index():
    return render_template('dashboard/dashboard_base.html')
