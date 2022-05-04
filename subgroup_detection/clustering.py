from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from pandas import Series

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