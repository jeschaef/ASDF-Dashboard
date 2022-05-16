import logging

from flask import Blueprint, jsonify, request, url_for, abort
from flask_login import login_required, current_user

from app.blueprints.util import load_data
from app.model import Dataset
from app.tasks import fairness_analysis, FairnessTask

task = Blueprint('task', __name__)
log = logging.getLogger()


@task.route('/task/fairness', methods=['POST'])
@login_required
def start_fairness_task():
    # Does the user already have a running task? If so, stop it before starting another
    current_task = FairnessTask.current()
    if current_task is not None:
        log.debug("Fairness task is already running")
        stop_fairness_task(current_task)

    # Get data from request body
    dataset_id = request.form.get("dataset_id")  # TODO no dataset id in request body
    dataset = Dataset.query.get(dataset_id)
    pos_label = int(request.form.get("positive_class"))
    threshold = float(request.form.get("threshold"))

    # Load data & serialize
    data = load_data(current_user.id, dataset_id)
    data_json = data.to_json()  # json serialization is required to send task

    # Start task
    task = fairness_analysis.delay(data_json, pos_label=pos_label, threshold=threshold)
    FairnessTask.cache(task)

    return jsonify({}), 202, {'status': url_for('task.status')}


@task.route('/task/fairness/status')
@login_required
def status():
    # Is user authorized to view this task?
    current_task = FairnessTask.current()
    if current_task is None:
        return abort(404)

    # Switch task state
    task = fairness_analysis.AsyncResult(current_task)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'status': 'Waiting for task to start...'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')  # task.info is a dict
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'status': 'Successfully finished task!',
            'result': task.info  # task.info is a json string (result)
        }
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)  # TODO return stream


def stop_fairness_task(current_task):
    # Delete cache entry
    FairnessTask.delete()

    # Revoke task (terminate if running already)
    fairness_analysis.AsyncResult(current_task).revoke(terminate=True)
    log.debug(f"Revoked task {current_task}")

