import logging

from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required, current_user

from app.blueprints.util import load_data
from app.model import Dataset
from app.tasks import fairness_analysis

task = Blueprint('task', __name__)
log = logging.getLogger()


@task.route('/task/fairness', methods=['POST'])
@login_required
def start_fairness_task():
    # Get data from request body
    dataset_id = request.form.get("dataset_id")     # TODO no dataset id in request body
    dataset = Dataset.query.get(dataset_id)
    pos_label = int(request.form.get("positive_class"))
    threshold = float(request.form.get("threshold"))

    # Load data & serialize
    owner = current_user.id
    data = load_data(owner, dataset_id)
    data_json = data.to_json()  # json serialization is required to send task

    # Start task
    task = fairness_analysis.delay(data_json, pos_label=pos_label, threshold=threshold)

    # fair_res = FairnessResult.from_json(task.get())
    # log.debug(f"Got fairness result: {fair_res}")

    return jsonify({}), 202, {'Location': url_for('task.status', task_id=task.id)}


@task.route('/task/<task_id>')
@login_required
def status(task_id):
    task = fairness_analysis.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'status': 'Waiting for task to start...'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')       # task.info is a dict
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'status': 'Successfully finished task!',
            'result': task.info                         # task.info is a json string (result)
        }
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)
