import logging

from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.cluster import KMeans
from sklearn.neighbors import KNeighborsClassifier
from pandas import Series, DataFrame
from shap import KernelExplainer
import numpy as np

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


def explain_clustering_shap(model, data, sample_frac=0.1, min_sample_size=10):
    """
    Explain a given clustering model using SHAP.
    :param model: Clustering model.
    :param data: The numerical dataset used to train the clustering model (preprocessed) without labels.
    :return: SHAP values for each instance grouped by cluster
    """
    cluster_shap = {}
    labels = model.labels_
    n_clusters = labels.max() + 1

    # Train a kmeans model for KernelExplainer background data
    kmeans = KMeans(n_clusters=n_clusters).fit(data)

    # Iterate over all clusters and explain them (one-vs-all)
    for c in range(0, n_clusters):

        # If the model is able to predict inputs, use this for KernelExplainer
        # Otherwise, train a k-NN model to predict cluster membership
        if can_predict(model):
            f = lambda X: (model.predict(X) == c).astype(int)  # one-vs-all approach (cluster ec vs rest)
        else:
            knn = KNeighborsClassifier(n_neighbors=7, weights='distance').fit(data, labels)
            f = lambda X: (knn.predict(X) == c).astype(int)

        # Get instances of cluster c
        indices = (labels == c).astype(int)
        clusterX = DataFrame(data.values[indices.astype(bool)], columns=data.columns)
        samples = clusterX.sample(frac=sample_frac)
        if len(samples) < min_sample_size:
            if len(clusterX) <= min_sample_size:
                samples = clusterX
            else:
                samples = clusterX.sample(n=min_sample_size)

        # Explain cluster c
        explainer = KernelExplainer(f, DataFrame(kmeans.cluster_centers_, columns=data.columns))
        shap_values = explainer.shap_values(samples)
        cluster_shap[c] = DataFrame(shap_values, columns=data.columns)

    return cluster_shap


def patterns_from_cluster_shap(cluster_shap, data, dataX, labels, shap_threshold=0.1, prefix_sep='#'):
    """
    Extract patterns (rules) from the SHAP explanations of the clustering model.
    :param cluster_shap: SHAP values of each instance grouped by cluster.
    :param data: The original dataset (not preprocessed).
    :param dataX: The numerical dataset used to train the clustering model (preprocessed) without labels.
    :param labels: Clustering labels.
    :param shap_threshold: Minimal mean SHAP value of a feature to be considered for a pattern.
    :return: Set of patterns for each cluster
    """
    cluster_patterns = {}
    for c in cluster_shap:

        # Get SHAP, mean SHAP and data instances of cluster c
        shap_vals = cluster_shap[c]
        mean_shap_vals = shap_vals.mean()
        indices = (labels == c).astype(int)
        cluster_data = DataFrame(dataX.values[indices.astype(bool)], columns=dataX.columns)

        # For each feature with mean SHAP value above the shap_threshold,
        # extract a pattern of the form 'feature =/!= value'
        patterns = []
        for fn in mean_shap_vals[mean_shap_vals > shap_threshold].keys():

            # Split the feature names according to the prefix_sep used in one-hot-encoding the data
            split = fn.split(prefix_sep, maxsplit=1)
            col = split[0]
            argmax = np.bincount(cluster_data[fn]).argmax()

            if len(split) == 1:  # not one-hot-encoded feature (not categorical)
                patterns.append((col, True, argmax))
            elif len(split) == 2:  # one-hot-encoded feature
                val = split[1]

                # If the one-hot-encoded feature is binary and the condition negated,
                # find the counter part (e.g. sex#M==0 --> sex != M --> sex=F).
                if argmax == 0:
                    orig_column = data.filter(like=col)
                    unq = np.unique(orig_column)  # unique values for original column (e.g. sex --> [M, F])
                    if len(unq) == 2:
                        counter_val = unq[0] if unq[1] == val else unq[1]
                        patterns.append((col, True, counter_val))
                    else:
                        patterns.append((col, False, val))
                else:
                    patterns.append((col, True, val))
        # Store patterns for cluster c
        cluster_patterns[c] = patterns

    return cluster_patterns


def can_predict(model):
    predict_op = getattr(model, "predict", None)
    return callable(predict_op)
