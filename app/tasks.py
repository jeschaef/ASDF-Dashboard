import pandas as pd
from celery import Task
from celery.utils.log import get_task_logger
from flask_login import current_user
from sklearn.cluster import KMeans

from app.cache import cache
from app.celery_app import celery_app
from subgroup_detection.fairness import test_model_fairness

log = get_task_logger(__name__)


class FairnessTask(Task):
    @staticmethod
    def _cache_key():
        return "fair_task_" + current_user.session_token

    @staticmethod
    def cache(task):
        cache.add(FairnessTask._cache_key(), task.id, timeout=0)  # no expiration

    @staticmethod
    def current():
        return cache.get(FairnessTask._cache_key())

    @staticmethod
    def delete():
        return cache.delete(FairnessTask._cache_key())

    def on_success(self, retval, task_id, args, kwargs):
        log.info("On success")
        self.delete()
        log.info("Uncached task")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        log.info("On failure")


# TODO cache results?
@celery_app.task(bind=True, base=FairnessTask)
def fairness_analysis(self, df_json, pos_label=1, threshold=0.65):

    log.info(f"Starting fairness analysis: pos_label={pos_label}, threshold={threshold}")

    def progress(status):
        self.update_state(state='PROGRESS', meta={'status': status})

    # Load data
    progress('Loading data ...')
    data = pd.read_json(df_json)        # deserialize json
    log.info(type(self))

    # Specify model
    # model = AgglomerativeClustering(n_clusters=50, linkage='single')
    model = KMeans(n_clusters=50)

    # Test fairness of the classification model
    fair_res = test_model_fairness(model, data, pos_label=pos_label, threshold=threshold, progress=progress)

    # Return result as json
    return fair_res.to_json()
