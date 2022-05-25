import logging

from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.cluster import KMeans, DBSCAN, OPTICS
from pandas import Series

log = logging.getLogger()

def validate_clustering(X, labels):
    """
    Compute different cluster validation indices.
    @param X: Numeric data
    @type X: pd.DataFrame or array
    @param labels: Cluster labels
    @type labels: list of int
    @return: Series containing CVI values
    @rtype: Series
    """
    sil = silhouette_score(X, labels)
    dbi = davies_bouldin_score(X, labels)
    chi = calinski_harabasz_score(X, labels)
    return Series(data={'sil': sil, 'dbi': dbi, 'chi': chi})


def choose_model(model_cls, param_dict):
    if model_cls is KMeans:
        return KMeans().set_params(**param_dict)
    elif model_cls is DBSCAN:
        return DBSCAN().set_params(**param_dict)
    elif model_cls is OPTICS:
        return OPTICS().set_params(**param_dict)

    log.error("Not matching")
    return None
