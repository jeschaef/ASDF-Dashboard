import logging

from flask import Blueprint, jsonify, request, url_for, abort
from flask_login import login_required, current_user
from sklearn.cluster import KMeans

from app.blueprints.util import load_data, get_param_dict
from app.decorators import confirmation_required
from app.model import Dataset
from app.tasks import fairness_analysis, FairnessTask

task = Blueprint('task', __name__)
log = logging.getLogger()


@task.route('/task/fairness', methods=['POST'])
@login_required
@confirmation_required
def start_fairness_task():
    # Does the user already have a running task? If so, stop it before starting another
    stopped = FairnessTask.stop(current_user)
    log.debug(f"Stopped current task? {stopped}")

    # Get data from request body
    dataset_id = request.form.get("dataset_id")  # TODO no dataset id in request body
    dataset = Dataset.query.get(dataset_id)
    pos_label = int(request.form.get("positive_class"))
    threshold = float(request.form.get("threshold"))
    categ_columns = request.form.getlist("categ_columns[]")
    if not categ_columns:                   # If not provided, set to None
        categ_columns = None

    algorithm = request.form.get("algorithm")
    parameters = request.form.getlist("parameters[]")
    values = request.form.getlist("values[]")
    param_dict = get_param_dict(algorithm, parameters, values)
    log.debug(f"{param_dict}")

    # Load data & serialize
    data = load_data(current_user.id, dataset_id)
    data_json = data.to_json()  # json serialization is required to send task

    # Start task
    t = fairness_analysis.delay(data_json, algorithm, pos_label=pos_label, threshold=threshold,
                                categ_columns=categ_columns, param_dict=param_dict)
    FairnessTask.cache(current_user, t.id)      # cache running task

    return jsonify({}), 202, {'status': url_for('task.status')}


@task.route('/task/fairness/status')
@login_required
@confirmation_required
def status():
    # Is there a current task?
    current_task_id = FairnessTask.get(current_user)
    if current_task_id is None:
        return abort(404)

    # Switch task state
    t = fairness_analysis.AsyncResult(current_task_id)
    if t.state == 'PENDING':
        # job did not start yet
        response = {
            'state': t.state,
            'status': 'Waiting for task to start...'
        }
    elif t.state == 'PROGRESS':
        response = {
            'state': t.state,
            'status': t.info.get('status', '')  # task.info is a dict
        }
    elif t.state == 'SUCCESS':
        response = {
            'state': t.state,
            'status': 'Successfully finished task!',
            'result': t.info  # task.info is a json string (result)
        }
        FairnessTask.delete(current_user)       # remove cache entry
    else:
        # something went wrong in the background job (states: FAILURE, RETRY, REVOKED)
        response = {
            'state': t.state,
            'status': str(t.info),  # this is the exception raised
        }
        # FairnessTask.delete(current_user)  # remove cache entry????

    return jsonify(response)  # TODO return stream
