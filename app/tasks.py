import pandas as pd
from celery.utils.log import get_task_logger
from sklearn.cluster import KMeans

from app.blueprints.util import load_data
from app.celery_app import celery_app
from subgroup_detection.fairness import test_model_fairness

log = get_task_logger(__name__)

# TODO cache results?
@celery_app.task()
def fairness_analysis(df_json, pos_label=1, threshold=0.65):
    data = pd.read_json(df_json)
    # model = AgglomerativeClustering(n_clusters=50, linkage='single')
    model = KMeans(n_clusters=50)
    log.info("fairness_analysis: Computed model")
    fair_res = test_model_fairness(model, data, pos_label=pos_label, threshold=threshold)
    return fair_res.to_json()

