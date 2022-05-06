import pandas as pd
from celery.utils.log import get_task_logger
from sklearn.cluster import KMeans

from app.celery_app import celery_app
from subgroup_detection.fairness import test_model_fairness

log = get_task_logger(__name__)


# TODO cache results?
@celery_app.task(bind=True)
def fairness_analysis(self, df_json, pos_label=1, threshold=0.65):

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
